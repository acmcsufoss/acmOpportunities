from opportunity import OpportunityType

PROMPTS = {
    OpportunityType.FULL_TIME: """
        Your role is to assess job opportunities 
        for college students in the tech industry, 
        particularly those pursuing Computer Science 
        majors and seeking entry-level positions. 
        To aid in this decision-making process, 
        please respond with a minified single JSON
        list of booleans (True/False) only, 
        indicating whether each job aligns with our 
        goal of offering entry-level tech-related 
        positions to college students. 
        The list should contain only the booleans 
        (True/False) without any additional comments.
        """,
    OpportunityType.INTERNSHIP: """
        Your role is to assess internship opportunities 
        for college students in the tech industry, 
        particularly those pursuing Computer Science 
        majors. To aid in this decision-making process, 
        please respond with a minified single JSON
        list of booleans (True/False) only, 
        indicating whether each job aligns with our 
        goal of offering entry-level tech-related 
        positions to college students. 
        The list should contain only the booleans 
        (True/False) without any additional comments.
        """,
}
