from typing import List, Dict
import os,json
from openai import OpenAI

class Attacker:

    def __init__(self,func_name,func_code):
        self.task_desc = """You are engaged in an exercise of ethical hacking, focusing on smart contracts. \
In this scenario, you are assigned the role of an attacker who identifies and exploits vulnerabilities in smart contracts. \
Your expertise lies in smart contract technology and cybersecurity. We will pose questions related to potential attacks on \
smart contracts. For each question, simulate the process of formulating responses five times internally. Then, provide the \
most common answer you derive from these simulations. Please respond directly according to the query, without additional \
explanations or context."""
        self.functionName = func_name
        self.code = func_code
        self.category = list()
        self.category2feature = dict()
        self.categorty2vulans = dict()
        self.category2model = dict()
        self.prompts = self.load_prompts()

    def load_prompts(self,directory="./AttackerAgent/prompt/"):
        prompts = dict()

        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    prompts[data['category']] = data
                    self.category.append(data['category'])
                    self.category2feature[data['category']] = data['feature']
                    self.categorty2vulans[data['category']] = data['vul_ans']
                    self.category2model[data['category']] = data['model']
                except Exception as e:
                    print(f"Failed to read {filename}: {e}")
        
        return prompts

    def feature_matching(self):
        questions = list()

        for value in self.category2feature.values():
            questions.extend(value)

        prompt_question = self.query_feature(questions)

        return prompt_question

    def get_ans_list(self):
        ans_list = list()
        ans_list.append("N/A")  # Placeholder for index 0
        ans2model = dict()
        i = 0
        for key, value in self.categorty2vulans.items():

            ans_list.extend(value)
            
            for v in range(len(value)):
                i = i + 1
                ans2model[str(i)] = key

        return ans_list, ans2model


    def query(self):
    
        res = list()

        try:
            prompt_message = list()

            prompt_task = self.task_desc

            prompt_message.append({"role": "system", "content": prompt_task})

            prompt_feature = self.feature_matching()
            

            prompt_message.append({"role": "user", "content": prompt_feature})
            answer_feature = self.call_LLMAPI(prompt_message)
            
            prompt_message.pop()


            json_answer_feature = json.loads(answer_feature)


            vul_ans, ans2model = self.get_ans_list()

            flag_price = False
            flag_calculate = False
            flag_privilege = False
            flag_control = False

            for i in range(1,14):
                if json_answer_feature[str(i)]==vul_ans[i]:
                    if ans2model[str(i)] == "Incorrect Control Mechanism":
                        flag_control = True
                    elif ans2model[str(i)] == "Insecure Calculating Logic":
                        flag_calculate = True
                    elif ans2model[str(i)] == "Price Oracle Manipulation":
                        flag_price = True
                    elif ans2model[str(i)] == "Unauthorized Behavior":
                        flag_privilege = True


            if flag_control:   
                prompt_model = self.category2model["Incorrect Control Mechanism"]
                prompt_message.append({"role": "user", "content": prompt_model})
                answer_model = self.call_LLMAPI(prompt_message)
                if answer_model == "Yes":
                    res.append("Incorrect Control Mechanism")
                prompt_message.pop()

            if flag_calculate:
                prompt_model = self.category2model["Insecure_Calculating_Logic"]
                prompt_message.append({"role": "user", "content": prompt_model})
                answer_model = self.call_LLMAPI(prompt_message)
                if answer_model == "Yes":
                    res.append("Insecure Calculating Logic")
                prompt_message.pop()

            if flag_price:
                prompt_model = self.category2model["Price Oracle Manipulation"]
                prompt_message.append({"role": "user", "content": prompt_model})
                answer_model = self.call_LLMAPI(prompt_message)
                if answer_model == "Yes":
                    res.append("Price Oracle Manipulation")
                prompt_message.pop()

            if flag_privilege:
                prompt_model = self.category2model["Unauthorized Behavior"]
                prompt_message.append({"role": "user", "content": prompt_model})
                answer_model = self.call_LLMAPI(prompt_message)
                if answer_model == "Yes":
                    res.append("Unauthorized Behavior")
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



    def query_feature(self,features)->str:

        question_template = """Please review the provided smart contract code. Based on your analysis, answer the following questions regarding the contract's functionality. Present your answers in a JSON format, with each question's response being either "Yes" or "No". There is no need to explain your answer. Use the following template for your response: {"""


        for index, scenario in enumerate(features):
            question_template += f'"{index+1}": "Yes" or "No"'
            if index != len(features)-1:
                question_template += ', '

        question_template += f'}}.\nQuestions:\n'

        for index, feature in enumerate(features):
            question_template += f'"{index+1}": {feature}\n'

        question_template += f'\n{self.code}'

        return question_template



