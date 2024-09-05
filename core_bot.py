from openai import OpenAI
from copy import deepcopy
import logger
import apikey
import json

client = OpenAI(api_key=apikey.api_key)
class Bot:
    def __init__(self,
    tools = [[],[]],
    model="gpt-4o",
    save_history=True,
    system_role="",
    stream=False,
    temperature=0,
    logging=True,
    max_tokens=1024):
        self.system_role = system_role
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.messages = []
        self.save_history = save_history
        self.stream = stream
        self.model = model
        self.tools = tools
        self.tool_calls = None
        self.logging = logging

        self.messages.append({"role": "system", "content": self.system_role})

    def set_model(self, model):
        self.model = model

    def show_chat(self):
        return self.messages
    
    def set_chat(self, new_messages):
        self.messages = new_messages

    def forget(self):
        self.messages = []
        self.messages.append({"role": "system", "content": self.system_role})

    def add_bot_msg(self, message):
        self.messages.append({"role": "assistant", "content": message})

    def add_user_msg(self, message):
        self.messages.append({"role": "user", "content": message})

    # Generator to yield streamed responses
    def stream_handler(self, response):
        bot_msg = "" 
        current_index = 0
        self.tool_calls = []
        func_call = {"tool_call":
                            {
                            "id":None,
                            "type": "function",
                            "function":{
                                "name": None,
                                "arguments": "",
                                },
                            },
                        }

        # Function Calls
        for chunk in response:
            delta = chunk.choices[0].delta.tool_calls
            chonk = chunk.choices[0].delta.content

            if delta:
                name = delta[0].function.name
                arguments = delta[0].function.arguments
                id = delta[0].id
                index = delta[0].index

                if index > current_index: # if new func call, add the previous call to self.tool_calls and start on the next one.
                    func_call_copy = deepcopy(func_call)
                    self.tool_calls.append(func_call_copy)
                    self.messages.append(
                            {"role": "assistant", 
                             "tool_calls": [func_call_copy["tool_call"]],
                            })
                    stream = self.run_tools()

                    for chonk in stream:
                        yield chonk

                    func_call['tool_call']['function']['arguments'] = ""
                    current_index = index

                if id:
                    func_call['tool_call']['id'] = id
                if name:
                    func_call['tool_call']['function']['name'] = name
                if arguments:
                    func_call['tool_call']['function']['arguments'] += arguments

            elif chunk.choices[0].finish_reason == "tool_calls":
                func_call_copy = deepcopy(func_call)
                self.tool_calls.append(func_call_copy)
                self.messages.append(
                            {"role": "assistant", 
                             "tool_calls": [func_call_copy["tool_call"]],
                            })
                stream = self.run_tools()

                for chonk in stream:
                    yield chonk

            elif chonk is not None:
                bot_msg += chonk
                yield chonk

            else:
                self.add_bot_msg(bot_msg)

    def run_tools(self):
        if self.tool_calls != None:
            available_functions = self.tools[1]
            # Step 4: send the info for each function call and function response to the model
            for tool_call in self.tool_calls:
                if self.stream:
                    function_name = tool_call['tool_call']['function']['name']
                    function_args = json.loads(tool_call['tool_call']['function']['arguments'])
                    tool_id = tool_call['tool_call']['id']
                else:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    tool_id = tool_call.id

                # Find the function to call
                function_to_call = available_functions[function_name]

                # Unpack the arguments and pass them to the function
                function_response = function_to_call(**function_args)

                self.messages.append(
                    {
                        "tool_call_id": tool_id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response

                if self.logging:
                    logger.log(f"FUNCTION: {function_name} -> {function_response}")
           
            function_interpretation = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                stream=self.stream,
                max_tokens=self.max_tokens
            )

            self.tool_calls = None

            if self.stream:
                # Return a generator for streamed responses
                return self.stream_handler(function_interpretation)
            else:
                bot_msg = function_interpretation.choices[0].message.content
                self.add_bot_msg(bot_msg)
                return bot_msg
        else:
            return None

    def prompt(self, prompt = None):
        if not self.save_history:
            self.messages = []
            self.messages.append({"role": "system", "content": self.system_role})

        self.add_user_msg(prompt)

        # TODO: Fix streaming function calls
        response = client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            stream=self.stream,
            max_tokens=self.max_tokens,
            tools=self.tools[0]
        )

        if self.stream:
            # Return a generator for streamed responses
            return self.stream_handler(response)

        # static case
        response_message = response.choices[0].message
        self.tool_calls = response_message.tool_calls
        self.messages.append(response_message)
        tool_response = self.run_tools()

        if tool_response:
            return tool_response #returns tool response if tools used
        return response_message.content #otherwise returns message
    
