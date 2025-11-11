
from typing import List, Dict
import os,json
from openai import OpenAI


class Auditor:

    def __init__(self,func_name,func_code):
        self.task_desc = """You are engaged in an exercise of code auditing, focusing on smart contracts. \
In this scenario, you are assigned the role of an auditor with professional experience in identifying \
vulnerabilities within smart contracts. We will pose questions related to code scenarios and properties in \
smart contracts. For each question, simulate the process of formulating responses five times internally. \
Then, provide the most common answer you derive from these simulations. Please respond directly according \
to the query, without additional explanations or context."""
        self.functionName = func_name
        self.code = func_code
        self.types = list()
        self.type2scenario = dict()
        self.type2property = dict()
        self.prompts = self.load_prompts()
        
    

    def load_prompts(self,directory="./AuditorAgent/prompt/"):
        prompts = dict()

        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    prompts[data['type']] = data
                    self.types.append(data['type'])
                    self.type2scenario[data['type']] = data['scenario']
                    self.type2property[data['type']] = data['property']
                except Exception as e:
                    print(f"Failed to read {filename}: {e}")
        
        return prompts
    



    def scenarios_matching(self)->str:

        questions = list()

        for value in self.type2scenario.values():
            questions.append(value)

        prompt_question = self.query_scenarios(questions,self.code)

        return prompt_question
    
    def property_matching(self,question:str)->str:

        prompt_question = self.query_property(question)
        
        return prompt_question

    def query(self):
    
        res = list()


        try:
            
            prompt_message = list()
            prompt_message.append({"role": "system", "content": self.task_desc})

            prompt_scenarios = self.scenarios_matching()


            prompt_message.append({"role": "user", "content": prompt_scenarios})

            answer_scenarios = json.loads(self.call_LLMAPI(prompt_message))
            

            prompt_message.pop()

            for i in range(10):
                if answer_scenarios[str(i+1)]=="Yes":
                    
                    prompt_property = \
                        self.property_matching(self.type2scenario[self.types[i]] + \
                                        " "+self.type2property[self.types[i]])


                    prompt_message.append({"role": "user", "content": prompt_property})
                
                    answer_property = self.call_LLMAPI(prompt_message)
                    
                    if answer_property == "Yes":
                        res.append(self.types[i])

                    prompt_message.pop()


                
        except Exception as e:
            print(e)



        return res



    def call_LLMAPI(self,prompt_question:list)->str:
        try:
            client = OpenAI(
                        api_key = os.getenv("OPENAI_API_KEY"),
                    )

            completion = client.chat.completions.create(
                        model = "gpt-4-1106-preview",
                        messages=prompt_question,
                        temperature = 0,
                        top_p = 1,
                        frequency_penalty = 0,
                        presence_penalty = 0,
                    )

        except Exception as e:
            print(e)
            print("LLM API EER")
            exit()

        answer = completion.choices[0].message.content
        answer = answer.replace("```json\n", "").replace("\n```", "")

        return answer

    

    def query_property(self,property) -> str:
        question_template = f"""Does the following smart contract code {property}? Answer only "Yes" or "No".\n{self.code}"""
        return question_template


    def query_scenarios(self,scenarios:List[str], code:str) -> str:
        question_template="""Given the following smart contract code, answer the questions below and organize the result in a json format like {"""
    
        for index, scenario in enumerate(scenarios):
            question_template += f'"{index+1}": "Yes" or "No"'
            if index != len(scenarios)-1:
                question_template += ', '

        question_template += f'}}.\n'

        for index, scenario in enumerate(scenarios):
            question_template += f'"{index+1}": Does it "{scenario}"?\n'
    
        question_template += f'\n{code}'
    
        return question_template
