# __________________________________CREATE_____________________________________

createSkillMutation = '''
    mutation createSkillMutation($name : String!, $language : String!) {
        skillCreate(data : {
            name : $name
            language : $language
        }) {
            id
            name
            language
        }
    }
'''

createRequirementMutation = '''
    mutation createRequirementMutation($description : String!, $language : String!, $type : [String!]) {
        requirementCreate(data : {
            description : $description
            language : $language
            type : $type
        }) {
            id
            description
            language
        }
    }
'''

createOccupationMutation = '''
    mutation createOccupationMutation($occID : String!, $name : String!, $overview : String!, $language : String!) {
        occupationCreate(data : {
            occID : $occID
            name : $name
            language : $language
            overview : $overview
        }) {
            id
            name
        }
    }
'''


createOccupationRequirementMutation = '''
    mutation createOccupationRequirementMutation($occID : String!, $description : String!, $relevance : String!) {
     occupationRequirementCreate(data : {
             occupations: {connect : {occID : $occID}}
            requirements : {connect : {description : $description}}
            relevance : $relevance 
        }) {
            id
        }
    }
'''


createSowMutation = '''
    mutation createSowMutation($title : String!, $description : String!, 
    $skills : String!, $requirements : String!, $feedback : String!,  $rating : String!) {
     sowCreate(data : {
             title: $title
             description: $description
             skills: $skills
             requirements : $requirements
             feedback: $feedback
             rating: $rating
        }) {
            id
        }
    }
'''


# __________________________________UPDATE_____________________________________

updateOccupationSkillsMutation = '''
    mutation updateOccupationSkillsMutation($skill : String!, $occID : String!) {
     occupationUpdate (data : {      
  			skills : {connect : {name : $skill}}
              }, 
        filter : {
        occID : $occID}) 
     {
     id
     occID
     }
    }
'''


updateOccupationRequirementsMutation = '''
    mutation updateOccupationRequirementsMutation($description : String!, $occID : String!) {
     occupationUpdate (data : {      
  			requirements : {connect : {description : $description}}
              }, 
        filter : {
        occID : $occID}) 
     {
     id
     occID
     }
    }
'''


# __________________________________QUERY______________________________________

getAllOccupationsQuery = '''
    query {
        occupationsList{
            count
            items {
                occID
              	name
                requirements {items {description}}
              	skills {items {name}
            }
        }
        }}
'''
