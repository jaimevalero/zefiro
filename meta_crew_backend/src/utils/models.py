import os
from typing import Optional

from crewai import LLM
from loguru import logger
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
# If DEBUG is set to 1, the LLM will print the request and response to the console.

if os.getenv("DEBUG",0) == "1":
    import litellm
    litellm.set_verbose=True # 👈 this is the 1-line change you need to make

from langchain_openai import ChatOpenAI

from llama_index.llms.ollama import Ollama as ollama_aux
#from llama_index.llms.openai import OpenAI
from llama_index.llms.ollama import Ollama

#from openai import OpenAI # Use for deepseek

# from langchain_community.llms.openai import OpenAI # NO VALE
# from langchain_openai.llms.base import OpenAI # NO VALE
from llama_index.core import Settings
from enum import Enum

class Provider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"



def get_provider(model_type) -> Provider:
    """
    Get the provider from the model name.
    
    Returns:
        Provider: The provider enum value.
    """
    model_type = model_type.upper()

    if model_type not in ["MAIN", "AUX", "EMBED"]:
        raise ValueError(f"Provider not recognized for model {model_type}")
    
    provider_string =  os.environ[f"{model_type}_PROVIDER"] 

    
    if "ollama" in provider_string:
        provider = Provider.OLLAMA
    elif "openai" in provider_string :
        provider = Provider.OPENAI
    elif "deepseek" in provider_string:
        provider = Provider.DEEPSEEK
    elif "openrouter" in provider_string:
        provider = Provider.OPENROUTER
    else:
        raise ValueError(f"Provider not recognized for model {provider_string}")
    
    #logger.info(f"Provider determined: {provider}")
    return provider

def get_api_key(model_type):
    """
    Retrieve the API key from the environment variable.

    Returns:
        str: The API key.
    """
    model_type = model_type.upper()
    if model_type not in ["MAIN", "AUX", "EMBED"]:
        raise ValueError(f"Provider not recognized for model {model_type}")
    
    return os.getenv(f"{model_type}_TOKEN", None)

    
def get_model_name(model_type):
    """
    Retrieve the embedding model name from the environment variable.

    Returns:
        str: The name of the embedding model. 
    """
    model_type = model_type.upper()
    if model_type not in ["MAIN", "AUX", "EMBED"]:
        raise ValueError(f"Provider not recognized for model {model_type}")
    
    if not os.getenv(f"{model_type}_MODEL_NAME"):
        entornos = str(os.environ.items())
        raise ValueError(f"{model_type}_MODEL_NAME environment variable not set {entornos}")
    return os.getenv(f"{model_type}_MODEL_NAME")

def get_api_base(model_type):
    """
    Retrieve the api name from the environment variable.

    Returns:
        str: The name of the api. 
    """
    model_type = model_type.upper()
    if model_type not in ["MAIN", "AUX", "EMBED"]:
        raise ValueError(f"Provider not recognized for model {model_type}")
    
    if not os.getenv(f"{model_type}_API_BASE"):
        raise ValueError(f"{model_type}_MODEL_NAME environment variable not set")
    return os.getenv(f"{model_type}_API_BASE")




def __get_model_embed():

    model_type = "EMBED"
    model_name = get_model_name(model_type)
    provider = get_provider(model_type)
    
    #provider =  Provider.OLLAMA
    if provider ==  Provider.OLLAMA :
        base_url = get_api_base(model_type) 
        logger.debug(f"Provider: {provider}, model_name: {model_name}, base_url: {base_url}")  
        embed_model = OllamaEmbedding(
                model_name=model_name.replace("ollama/", ""),
                base_url=base_url,
                num_ctx=8192,
                request_timeout=3600,
                keep_alive="25m",
                ollama_additional_kwargs={
                    "prostatic": 0, 
                    "num_ctx" : 8192},
            )      
    elif provider == Provider.OPENAI:
        api_key = get_api_key(model_type)
        logger.debug(f"Provider: {provider}, model_name: {model_name}, api_key: {api_key}")
        # export OPENAI_API_KEY env variable
        os.environ['OPENAI_API_KEY'] = api_key
        logger.debug(f"OPENAI_API_KEY exported")
        embed_model =OpenAIEmbedding(
                model_name=model_name.replace("openai/", ""),
                api_key=api_key,
                #api_base=base_url,
                num_ctx=8192,
                request_timeout=3600,
                keep_alive="25m")
    elif provider == Provider.OPENROUTER:
        api_key = get_api_key(model_type)
        logger.debug(f"Provider: {provider}, model_name: {model_name}, api_key: {api_key}")
        # export OPENAI_API_KEY env variable
        os.environ['OPENAI_API_KEY'] = api_key
        logger.debug(f"OPENAI_API_KEY exported")
        embed_model =OpenAIEmbedding(
                model_name=model_name.replace("openai/", ""),
                api_key=api_key,
                base_url=base_url,
                num_ctx=16384,
                request_timeout=3600,
                keep_alive="25m")        
    else:
        raise ValueError(f"Provider not recognized for model")

    
    return embed_model


def __get_model_aux():
    model_type = "AUX"

    model_name = get_model_name(model_type)
    base_url = get_api_base(model_type)   
    provider = get_provider(model_type) 
    if provider ==  Provider.OLLAMA :
        logger.debug(f"Provider: {provider}, model_name: {model_name}, base_url: {base_url}")
        llm = Ollama(
            model=model_name.replace("ollama/", ""),
            base_url = base_url,
            num_ctx=1024*32,
            context_window=1028*8,
            request_timeout=3600,
            keep_alive="25m"
            )
        
    elif provider == Provider.DEEPSEEK:
        api_key = get_api_key(model_type)
        # DeepSeek is open ai compatible, so we can use the open ai model
        llm = ChatOpenAI(
                    model="deepseek-chat", 
                    openai_api_key=api_key, 
                    openai_api_base='https://api.deepseek.com',
                    max_tokens=8192        )  
                
    elif provider == Provider.OPENROUTER:
        logger.debug(f"Provider: {provider}, model_name: {model_name}, base_url: {base_url}")
        api_key = get_api_key(model_type)
        os.environ["OPENROUTER_API_KEY"] = api_key
        from llama_index.llms.openrouter import OpenRouter
        llm = OpenRouter(
            api_key=api_key,
            max_tokens=8192       ,
            context_window=4096*8,
            model=model_name,
        )


    else:
        raise ValueError(f"Provider not recognized for model {provider}")
    return llm 

def get_model(model_type):
    """ Get LLM model. There are two dimensions to consider
    - model_type: "MAIN", "AUX", "EMBED" 
        "MAIN": for the llm for agents.
        "AUX": for the llm for tools and taking to embeddings.
        "EMBED": for the embeddings.
    
    Each domain, contains a configuration for the provider, model_name, the url for the endpoint and the api key.
    - Provider (class): Cloud provider for the model. 
        "ollama": for Ollama.
        "openai": for OpenAI.
        "deepseek": for DeepSeek (Alibaba).
    """
    if model_type == "EMBED":
        return __get_model_embed()
    elif model_type == "AUX":
        return __get_model_aux()
    
    model_name = get_model_name(model_type)
    base_url = get_api_base(model_type)   
    provider = get_provider(model_type) 
    if provider ==  Provider.OLLAMA :
        llm = Ollama(
            model=model_name.replace("ollama/", ""),
            base_url = base_url,
            num_ctx=1024*32,
            context_window=1028*8,
            request_timeout=3600,
            keep_alive="25m"
            )
    elif provider == Provider.DEEPSEEK:
        api_key = get_api_key(model_type)
        os.environ['DEEPSEEK_API_KEY'] = api_key
        llm = LLM(model=model_name,
                  max_tokens=16384,
                  timeout=25*60,
                  )

    elif provider == Provider.OPENROUTER:
        logger.debug(f"Provider: {provider}, model_name: {model_name}, base_url: {base_url}")
        api_key = get_api_key(model_type)
        os.environ["OR_SITE_URL"] = "" # optional
        os.environ["OR_APP_NAME"] = "" # optional
        #os.environ["OPENROUTER_API_KEY"] = api_key
        llm = LLM(model=model_name,
                  timeout=25*60,
                  api_key=api_key,
                  base_url=base_url
                  )

    else:
        raise ValueError(f"Provider not recognized for model {provider}")

    return llm

# if main, execute __get_model_embed()

# if __name__ == "__main__":
#     from gifted_children_helper.utils.secrets import load_secrets  # Import the moved function

# # Call load_secrets to initialize secrets
#     load_secrets()    
#     __get_model_embed()