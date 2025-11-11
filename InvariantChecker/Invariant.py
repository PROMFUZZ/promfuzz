import os,json
from openai import OpenAI


class Invariant:
    def __init__(self, func_name,contract_path,func_code):

        self.functionName = func_name
        self.code = func_code
        self.contract_path = contract_path
        self.prompts = self.load_prompts()
    
    def load_prompts(self,directory="./InvariantChecker/prompt/"):
        prompts = dict()

        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    prompts[data['type']] = data
                except Exception as e:
                    print(f"Failed to read {filename}: {e}")
        
        return prompts

    def checker(self,ptype):

        checkertype =  self.prompts[ptype]["checker"]


        if checkertype == "PriceChange_Checker(V1)":
            func_code_wc = self.generate_pricechange_checker(ptype)
        elif checkertype == "ExchangeRate_Checker(V1,V2)":
            func_code_wc = self.generate_exchangeRate_checker(ptype)
        elif checkertype == "TokenChange_Checker(V1,V2,V3)":
            func_code_wc = self.generate_tokenchange_checker(ptype)
        elif checkertype == "StatementOrder_Checker(S1,S2)":
            func_code_wc = self.generate_statementorder_checker(ptype)
        elif checkertype == "ShareSafety_Checker(V1,V2,V3)":
            func_code_wc = self.generate_sharesafety_checker(ptype)
        elif checkertype == "StateChange_Checker(V1,V2,S1)":
            func_code_wc = self.generate_statechange_checker(ptype)
        else:
            return None
        
        if func_code_wc == None:
            return None

        return self.insert_checker(self.contract_path, "InvariantChecker/FuzzLand.sol", self.code, func_code_wc)

    def generate_pricechange_checker(self,ptype):

        que_v1 = self.prompts[ptype]["V1"]

        prompt_v1 = self.prompt_var(que_v1)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v1})
        v1 = self.call_LLMAPI(prompt_message)

        if v1 == "None":
            return None
        
        checker_template_1 = f'''uint256 oldprice = 0;
bool invariant_flag = true;
        '''

        checker_template_2 = f'''if(invariant_flag){'{'}
    invariant_flag = false;
{'}'}else if(10*{v1}<=8*oldprice||10*{v1}>=12*oldprice){'{'}
    FuzzLand.typed_bug("{ptype}");
{'}'}
oldprice = {v1};
'''
        
        insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert "checker code" right before the end of the function.
function code:
{self.code}
checker code:
{checker_template_2}
Please provide the modified function code only without any additional explanation.
'''
        prompt_message = list()
        prompt_message.append({"role":"user","content":insert_prompt})
        modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")
        return checker_template_1+'\n'+modified_code
        
    def generate_exchangeRate_checker(self,ptype):    

        ques_v1 = self.prompts[ptype]["V1"]
        ques_v2 = self.prompts[ptype]["V2"]
        prompt_v1 = self.prompt_var(ques_v1)
        prompt_v2 = self.prompt_var(ques_v2)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v1})
        v1 = self.call_LLMAPI(prompt_message)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v2})
        v2 = self.call_LLMAPI(prompt_message)

        if v1 == "None" or v2 == "None":
            return None
        
        checker_template_1 = f'''uint256 oldrate = 0;
bool invariant_flag = true;'''
        
        checker_template_2 = f'''if(invariant_flag){'{'}
    invariant_flag = false;
{'}'}
else if(10*{v2}/{v1}<=8*oldrate||10*{v2}/{v1}>=12*oldrate){'{'}
    FuzzLand.typed_bug("{ptype}");
{'}'}
oldrate = {v2}/{v1};'''
        
        insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert "checker code" right before the end of the function.
function code: 
{self.code}
checker code:
{checker_template_2}
Please provide the modified function code only without any additional explanation.
'''
        prompt_message = list()     
        prompt_message.append({"role":"user","content":insert_prompt})
        modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")
        return checker_template_1+'\n'+modified_code
     
    def generate_tokenchange_checker(self,ptype):
        ques_v1 = self.prompts[ptype]["V1"]
        ques_v2 = self.prompts[ptype]["V2"]
        ques_v3 = self.prompts[ptype]["V3"]
        prompt_v1 = self.prompt_var(ques_v1)
        prompt_v2 = self.prompt_var(ques_v2)
        prompt_v3 = self.prompt_var(ques_v3)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v1})
        v1 = self.call_LLMAPI(prompt_message)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v2})
        v2 = self.call_LLMAPI(prompt_message)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v3})
        v3 = self.call_LLMAPI(prompt_message)

        if v1 == "None" or v2 == "None" or v3 == "None":
            return None

        if ptype == "Approval Not Clear":
            checker_template_1 = f'''uint256 oldallowed;
oldallowed = {v2}[{v1}][msg.sender];'''

            checker_template_2 = f'''if({v2}[{v1}][msg.sender]+{v3}!=oldallowed){'{'} 
    FuzzLand.typed_bug("{ptype}");
{'}'}'''



            insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert "checker code 1" right after the beginning of the function, and insert "checker code 2" right before the end of the function.
function code:
{self.code}
checker code 1:        
{checker_template_1}
checker code 2:
{checker_template_2}
Please provide the modified function code only without any additional explanation.
'''
            prompt_message = list()
            prompt_message.append({"role":"user","content":insert_prompt})
            modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")

            return modified_code

        elif ptype == "Unauthorized Transfer":
            checker_template = f'''if({v1}!=msg.sender&&{v2}[{v1}][msg.sender]<{v3}){'{'}
FuzzLand.typed_bug("{ptype}");
{'}'}'''    

            insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert the "checker code" right after beginning of the function.
function code:
{self.code}
checker code:        
{checker_template}
Please provide the modified function code only without any additional explanation.
'''
            prompt_message = list()
            prompt_message.append({"role":"user","content":insert_prompt})
            modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")

            return modified_code
        
        elif ptype == "Wrong Implementation of Amount Lock":
            checkker_template_1 = f'''if({v1}+{v2}!={v3}){'{'}
    FuzzLand.typed_bug("{ptype}");
{'}'}'''
            checker_template_2 = f'''if({v1}-{v2}!={v3}){'{'}
    FuzzLand.typed_bug("{ptype}");
{'}'}'''
            insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert "checker code 1" right after the statement of increasing locked tokens, and insert "checker code 2" right after the statement of decreasing locked tokens.
function code:
{self.code}
checker code 1:
{checkker_template_1}
checker code 2:
{checker_template_2}
Please provide the modified function code only without any additional explanation.
'''
            prompt_message = list()
            prompt_message.append({"role":"user","content":insert_prompt})
            modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")

            return modified_code

        elif ptype == "Improper Handling of Deposit Fee":
            checker_template = f'''if({v1}=={v2}+{v3}&&{v3}!=0){'{'}
    FuzzLand.typed_bug("{ptype}");
{'}'}'''
            insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert the "checker code" right before the end of the function.
function code:
{self.code}
checker code:
{checker_template}
Please provide the modified function code only without any additional explanation. 
'''
            prompt_message = list()
            prompt_message.append({"role":"user","content":insert_prompt})
            modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")

            return modified_code
            
    def generate_statementorder_checker(self,ptype):

        ques_s1 = self.prompts[ptype]["S1"]
        ques_s2 = self.prompts[ptype]["S2"]
        prompt_s1 = self.prompt_statement(ques_s1)
        prompt_s2 = self.prompt_statement(ques_s2)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_s1})
        s1 = self.call_LLMAPI(prompt_message)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_s2})
        s2 = self.call_LLMAPI(prompt_message)

        if s1 == "None" or s2 == "None":
            return None
        
        
        checker_template_1 = '''bool invariant_flag = false;'''

        checker_template_2 = f'''if(!invariant_flag){'{'}
    FuzzLand.typed_bug("{ptype}");
{'}'}'''
        checker_template_3 = "invariant_flag = true;"

        insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert "checker code 1" right before the statement "{s2}", and insert "checker code 2" right after the statement "{s1}".
function code:
{self.code}
checker code 1:
{checker_template_2}
checker code 2:
{checker_template_3}
Please provide the modified function code only without any additional explanation.  
'''
        prompt_message = list()
        prompt_message.append({"role":"user","content":insert_prompt})
        modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")
        return checker_template_1+'\n'+modified_code

    def generate_sharesafety_checker(self,ptype):
        ques_v1 = self.prompts[ptype]["V1"]
        ques_v2 = self.prompts[ptype]["V2"]
        ques_v3 = self.prompts[ptype]["V3"]
        prompt_v1 = self.prompt_var(ques_v1)
        prompt_v2 = self.prompt_var(ques_v2)
        prompt_v3 = self.prompt_var(ques_v3)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v1})
        v1 = self.call_LLMAPI(prompt_message)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v2})
        v2 = self.call_LLMAPI(prompt_message)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v3})
        v3 = self.call_LLMAPI(prompt_message)


        if v1 == "None" or v2 == "None" or v3 == "None":
            return None
        
        checker_template = f'''if({v1}==0&&{v2}=={v3}){'{'}
    FuzzLand.typed_bug("{ptype}");
{'}'}
'''
        insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert "checker code" right before the end of the function.
function code:
{self.code}
checker code:
{checker_template}
Please provide the modified function code only without any additional explanation.
'''
        prompt_message = list()
        prompt_message.append({"role":"user","content":insert_prompt})
        modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")
        return modified_code

    def generate_statechange_checker(self,ptype):
        ques_v1 = self.prompts[ptype]["V1"]
        ques_v2 = self.prompts[ptype]["V2"]
        ques_s1 = self.prompts[ptype]["S1"]
        prompt_v1 = self.prompt_var(ques_v1)
        prompt_v2 = self.prompt_var(ques_v2)
        prompt_s1 = self.prompt_statement(ques_s1)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v1})
        v1 = self.call_LLMAPI(prompt_message)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_v2})
        v2 = self.call_LLMAPI(prompt_message)
        prompt_message = list()
        prompt_message.append({"role":"user","content":prompt_s1})
        s1 = self.call_LLMAPI(prompt_message)

        if v1 == "None" or v2 == "None" or s1 == "None":
            return None
        
        checker_template_1 = f'''uint256 old_balance = 0;
bool invariant_flag = true;'''
        
        checker_template_2 = f'''if(invariant_flag){'{'}
    invariant_flag = false;
{'}'}else if({v1}.balanceOf(address(this))!=old_balance+{v2}){'{'}
    FuzzLand.typed_bug("{ptype}");
{'}'}
'''
        checker_template_3 = f'''
old_balance = {v1}.balanceOf(address(this));
'''     
        insert_prompt = f'''Please help me insert the following invariant checker into the function code. Specifically, insert "checker code 1" right before the statement "{s1}", and insert "checker code 2" right after the statement "{s1}".
function code:
{self.code}
checker code 1:
{checker_template_2}
checker code 2:
{checker_template_3}
Please provide the modified function code only without any additional explanation.
'''     
        prompt_message = list()
        prompt_message.append({"role":"user","content":insert_prompt})
        modified_code = self.call_LLMAPI(prompt_message).replace("```solidity\n", "")
        return checker_template_1+'\n'+modified_code
        
    def prompt_var(self,que):
        question_template = f"""In the following code, which variable is used to store {que}?

{self.code}

Please provide only the variable name without any additional explanation. If there is no such variable, respond with 'None'.
"""
        
        return question_template
    
    def prompt_statement(self,que):
        statement_template = f"""In the following code, which statement is {que}?

{self.code}

Please provide only the statement without any additional explanation. If there is no such statement, respond with 'None'.
"""
        return statement_template

    def insert_checker(self,target_sol, fuzzland_sol, func_code, modified_code):


        if not os.path.exists('./insertdir/'):
            os.makedirs('./insertdir/')
        
        for name in os.listdir('./insertdir/'):
            path = os.path.join('./insertdir/', name)
            if os.path.isfile(path):
                os.remove(path)

        with open(target_sol, "r", encoding="utf-8") as f:
            text = f.read()

        text = text.replace(func_code, modified_code, 1)

        with open(fuzzland_sol, "r", encoding="utf-8") as f:
            fuzz_code = f.read()

        lines = text.splitlines(True)
        out = []
        inserted = False

        for line in lines:
            out.append(line)
            if not inserted and line.strip().startswith("pragma solidity"):
                out.append("\n// Inserted FuzzLand.sol\n")
                out.append(fuzz_code)
                out.append("\n")
                inserted = True

        if not inserted:
            out = ["// Inserted FuzzLand.sol\n", fuzz_code, "\n"] + out

        new_path = './insertdir/'+target_sol.replace(".sol", "_patched.sol")

        with open(new_path, "w", encoding="utf-8") as f:
            f.write("".join(out))

        return new_path

    

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