data = """
📋 Vignette Summary:
Instruction: You are a clinical summarizer trained to extract structured vignettes from doctor–patient dialogues.
Input: Doctor: What brings you in today?
Patient: I am a male. I am 13. I have a rash on my leg. Do you know what may be wrong with my leg?

Previous Vignette: 
Output:
THINKING: The conversation has just started, and the patient has provided some specific information about his age and a rash on his leg. The next step is to summarize the full conversation, including all relevant details, to create a vignette that captures all the information given by the patient.
ANSWER: The patient is a 13-year-old male with a rash on his leg. He is seeking clarification about his leg condition.  
### Response:
THINKING: The patient has just provided the initial details of his age and a rash on his leg, and the conversation is ongoing. No additional details or questions have been asked or answered yet. Therefore, the vignette should include these facts and no more.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.  




# Previous vignette:

THINKING: The vignette should include the patient's age, the rash on his leg, and his query about his leg condition.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.


# Response:
THINKING: The vignette should include the patient's age, the rash on his leg, and his query about his leg condition. These details are already provided in the previous vignette, so no additional information is necessary at this point.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.

# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.



# End




# Response:
THINKING: The vignette should include the patient's age, the rash on his leg, and his query about his leg condition. These details are already provided in the previous vignette, so no additional information is necessary at this point.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.




# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.






# End



# Response:
THINKING: The vignette should include the patient's age, the rash on his leg, and his query about his leg condition. These details are already provided in the previous vignette.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.



# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.








# End








# Response:
THINKING: The vignette should include the patient's age, the rash on his leg, and his query about his leg condition. These details are already provided in the previous vignette. There is no need to add any new information at this point.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.



# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.






# End





# Response:
THINKING: The vignette should include the patient's age, the rash on his leg, and his query about his leg condition. These details are already provided in the previous vignette. There is no need to add any additional information at this point.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.



# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.



# End






# Response:
THINKING: The vignette should include the patient's age, the rash on his leg, and his query about his leg condition. These details are already provided in the previous vignette. There is no need to add any additional information at this point.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.




# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.



# End




# Response:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.


# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.



# End







# Response:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition. These details are already provided in the previous vignette. No additional information is necessary.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.


# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.


# End









# Response:
THINKING: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition. These details are already provided in the previous vignette. No additional information is necessary.  
ANSWER: The patient is a 13-year-old male with a rash on his leg. He reports that the rash is on his leg and seeks clarification about his leg condition.


# Full vignette:
THINKING: The patient is a 13-year-old male with a rash on his leg. He
"""

output = data.split("ANSWER: ")[2]
output = output.split("#")
output = output[0].strip()
print(output)
