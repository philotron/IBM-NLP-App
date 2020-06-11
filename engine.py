"""
    Matching engine of StaffingAdvisor
    ~~~~~
    The matching engine takes the user input along with the taxonomy data in 
    order to preprocess input, calculate matching scores and store the results. 
    
    Version 1.0 - 01.05.2019
"""

import json
import pandas as pd
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from spellchecker import SpellChecker
import Stemmer
from pp_const import replacements, special_chars, stopwords


class OccMatcher:
    """
        Occupation matcher class with all needed variables and methods
        
        Naming: inp=input, out=output, desc=description, taxon=taxonomy, df=dataframe,
        fuzzy_res=title matching results, tfidf_res=description matching results,
        skill_rank=sorted skill_list, th=threshold, coss=cosine similarity
    """

    def __init__(self, title, description, taxon=None):
        self.title_inp = title
        self.desc_inp = description
        self.taxon = taxon
        self.taxon_idx = None
        self.df = None
        self.fuzzy_res = []
        self.tfidf_res = []
        self.top_res = []
        self.title_out = None
        self.desc_out = None
        self.top_out = None
        self.skill_list = None
        self.skill_rank = None
        self.requirement_list = None
    

#__________________________________1._DATA_INPUT_______________________________
    # read in taxonomy json string and preprocess it
    def read_taxonomy(self, json_str):
        taxon_dict = json.loads(json_str)
        count = taxon_dict['data']['occupationsList']['count']
        self.taxon = pd.DataFrame.from_records(
                taxon_dict['data']['occupationsList']['items'])
        
        self.taxon_idx = self.taxon.index.tolist()
        self.taxon['name'] = self.taxon['name'].str.lower()
        self.taxon['desc'] = ''
        
        # restructure data for later usage
        for i in self.taxon_idx:
            self.taxon.at[i, 'skills'] = {k: [d.get(k) for d in 
                         self.taxon['skills'][i]['items']] 
            for k in set().union(*self.taxon['skills'][i]['items'])}
            self.taxon.at[i, 'requirements'] = {k: [d.get(k) for d in 
                         self.taxon['requirements'][i]['items']] 
            for k in set().union(*self.taxon['requirements'][i]['items'])}
           
        for i in self.taxon_idx:
            desc =''
            if self.taxon['skills'][i]:
                desc += ' '.join(self.taxon['skills'][i]['name']) + ' '
            if self.taxon['requirements'][i]:
                desc += ' '.join(self.taxon['requirements'][i]['description']) + ' '
            self.taxon.at[i, 'desc'] = desc.strip()
                 
        
        # apply replacement rules 
        for c in special_chars:
            self.taxon['name'] = self.taxon['name'].str.replace(c, ' ')    
        self.taxon['name'] = self.taxon['name'].str.replace('\s+', ' ', regex=True)
        self.taxon['name'] = self.taxon['name'].str.strip()
        
        stemmer = Stemmer.Stemmer('en')
        stem_stopwords = stemmer.stemWords(stopwords)
        
        # remove stepwords and apply stemming
        for w in stopwords:
          self.taxon['desc'] = self.taxon['desc'].str.replace(r'\b'+w+r'\b', ' ', regex=True)
        for c in special_chars:
           self.taxon['desc'] =self.taxon['desc'].str.replace(c, ' ')
        self.taxon['desc'] = self.taxon['desc'].str.replace('\s+', ' ', regex=True)
        self.taxon['desc'] = self.taxon['desc'].str.strip()
        self.taxon['desc'] = self.taxon['desc'].apply(lambda x: ' '.join(stemmer.stemWords(x.split())))
        for w in stem_stopwords:
          self.taxon['desc'] = self.taxon['desc'].str.replace(r'\b'+w+r'\b', ' ', regex=True)
        self.taxon['desc'] = self.taxon['desc'].str.replace('\s+', ' ', regex=True)
        self.taxon['desc'] = self.taxon['desc'].str.strip()
        
        # write preprocessed taxonomy into json string
        # directly reading in this file during instanciation will boost performance
        self.taxon.to_json(r'taxon.json', orient='split')
        

    # preprocess user input according to same rules as with taxonomy
    def preprocess_input(self):
        stemmer = Stemmer.Stemmer('en')
        stem_stopwords = stemmer.stemWords(stopwords)
        self.df = pd.DataFrame(columns=['title_inp', 'desc_inp'])
        self.df.loc[len(self.df)]=[self.title_inp.lower(), self.desc_inp.lower()] 

        # apply spelling correction
        spell = SpellChecker()
        self.df['title_inp'][0] = ' '.join([w.replace(w, spell.correction(w)) for w in (self.df['title_inp'][0].split())])

        # apply replacement rules on specified columns    
        for c in special_chars:
            self.df['title_inp'] = self.df['title_inp'].str.replace(c, ' ')

        for k, v in replacements.items():
            for i in v:
                self.df['title_inp'] = self.df['title_inp'].str.replace(r'\b'+i+r'\b', k, regex=True)
        self.df['title_inp'] = self.df['title_inp'].str.replace('\s+', ' ', regex=True)
        self.df['title_inp'] = self.df['title_inp'].str.strip()
           
        for w in stopwords:
          self.df['desc_inp'] = self.df['desc_inp'].str.replace(r'\b'+w+r'\b', ' ', regex=True)
        for c in special_chars:
           self.df['desc_inp'] =self.df['desc_inp'].str.replace(c, ' ')
        self.df['desc_inp'] = self.df['desc_inp'].str.replace('\s+', ' ', regex=True)
        self.df['desc_inp'] = self.df['desc_inp'].str.strip()
        self.df['desc_inp'] = self.df['desc_inp'].apply(lambda x: ' '.join(stemmer.stemWords(x.split())))
        for w in stem_stopwords:
          self.df['desc_inp'] = self.df['desc_inp'].str.replace(r'\b'+w+r'\b', ' ', regex=True)
        self.df['desc_inp'] = self.df['desc_inp'].str.replace('\s+', ' ', regex=True)
        self.df['desc_inp'] = self.df['desc_inp'].str.strip()
        
    def evaluate_match(self, th_fuzz=0.8, th_coss=0.1, th_fuzz_2=15, th_coss_2=0.2):
        #______________________________2._MATCHING_ALGORITHM___________________________
        
        #________________________________2.1_TITLE_MATCHING____________________________
        
        # Match title with title from taxonomy - first exact matching, followed by fuzzy matching
        self.taxon_idx = self.taxon.index.tolist()
        
        if self.df['title_inp'][0]:
            id_set = set()
            for j in self.taxon_idx:
                if self.df['title_inp'][0].startswith(self.taxon['name'][j]) \
                or self.taxon['name'][j].startswith(self.df['title_inp'][0]):
                    self.fuzzy_res.append((self.taxon['occID'][j], self.taxon['name'][j], 1))
                    id_set.add(self.taxon['occID'][j])
                if self.taxon['occID'][j] not in id_set \
                and (fuzz.token_set_ratio(self.df['title_inp'][0], self.taxon['name'][j]) >= (th_fuzz*100)): 
                    self.fuzzy_res.append((self.taxon['occID'][j], self.taxon['name'][j], round(fuzz.token_set_ratio(self.df['title_inp'][0], self.taxon['name'][j])/100, 3)))
        
            # handle multiple matches by sorting them
            # delete remaining matches if threshold bigger than th_fuzz_2 
            if len(self.fuzzy_res) > 1:
                 self.fuzzy_res = sorted(self.fuzzy_res, key=lambda tup: tup[2],reverse=True)
                 if (self.fuzzy_res[0][2] - self.fuzzy_res[1][2]) >= th_fuzz_2:
                     self.fuzzy_res = [self.fuzzy_res[0]] 
        
       
        
        #__________________________2.2_DESCRIPTION_MATCHING____________________________
        
        # initialize corpus with all requirement descriptions
        corpus = ['']
        for j in self.taxon_idx:
            corpus.append(self.taxon['desc'][j])
        
        # calculate tf-idf vectors     
        vectorizer = TfidfVectorizer()
        if self.df['desc_inp'][0]:
            corpus[0] = self.df['desc_inp'][0]             
            vector = vectorizer.fit_transform(corpus)
            matrix = cosine_similarity(vector[0:1], vector)
            for j in self.taxon_idx:
                if matrix[0][j+1] >= th_coss:
                    self.tfidf_res.append((self.taxon['occID'][j], self.taxon['name'][j], round(matrix[0][j+1], 3)))
            
         
            # handle multiple matches by sorting them
            # delete remaining matches if threshold bigger than th_coss_2 
            if len(self.tfidf_res) > 1:
                 self.tfidf_res = sorted(self.tfidf_res, key=lambda tup: tup[2],reverse=True)
                 if (self.tfidf_res[0][2] - self.tfidf_res[1][2]) >= th_coss_2:
                     self.tfidf_res = [self.tfidf_res[0]]         
        
        # calculate top matching results by using title and description results
        self.top_res = sorted([(a,b,(c * f)) for (a,b,c) in self.fuzzy_res 
                                    for (d,e,f) in self.tfidf_res  if ((a==d) and
                                         (b==e))], key=lambda tup: tup[2], reverse=True)     

    
    # function that calculates cosine similarity between a string and a list of
    # strings - it is used for example to find matching requirement descriptions
    # for a given string of skills
    def string_similarity(string, string_list, th_coss=0.15):
        result_list = []
        vectorizer = TfidfVectorizer()
        corpus = [string] + string_list
        vector = vectorizer.fit_transform(corpus)
        matrix = cosine_similarity(vector[0:1], vector)
        for j in range(len(string_list)):
            if matrix[0][j+1] >= th_coss:
                result_list.append((string_list[j], round(matrix[0][j+1], 3)))
            result_list = sorted(result_list, key=lambda tup: tup[1],reverse=True)
        return result_list
    
    
    
    # transform matching results into a amenable dataframe structure
    def output_results(self):
        #_________________________________3.DATA_OUTPUT________________________________
        
        self.title_out = pd.DataFrame(columns=['occID', 'name', 'score'])
        self.desc_out = pd.DataFrame(columns=['occID', 'name', 'score'])
        self.top_out = pd.DataFrame(columns=['occID', 'name', 'score'])
        
        for i in self.fuzzy_res:
            self.title_out.loc[len(self.title_out)] = list(i)
        for i in self.tfidf_res:
            self.desc_out.loc[len(self.desc_out)] = list(i)
        for i in self.top_res:
            self.top_out.loc[len(self.top_out)] = list(i)
            
        # get all skills and requirements from those occupations that appeared 
        # in the matching results - those IDs are stored in occ_id
        occ_id = list(set(self.title_out['occID']) | set(self.desc_out['occID']))
        res = self.taxon.query('occID in @occ_id') 
        
        self.skill_list = res['skills'].tolist()
        self.skill_list = [d['name'] for d in self.skill_list if 'name' in d]
        self.skill_list = [item for sublist in self.skill_list for item in sublist]
        self.skill_rank = list(set([(item, self.skill_list.count(item)) for item in self.skill_list if self.skill_list.count(item) > 1]))
        
        self.requirement_list = res['requirements'].tolist()
        self.requirement_list = [d['description'] for d in self.requirement_list if 'description' in d]
        self.requirement_list = list(set([item for sublist in self.requirement_list for item in sublist]))
        
        self.title_list = sorted(list(zip(res['occID'], res['name'])), key=lambda tup: tup[0])      
         
    
            
        return self
        
        
        


