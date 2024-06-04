from os import getenv
from typing import Type
from cat.log import log
from pydantic import BaseModel, ConfigDict
from cat.factory.custom_authorizator import BaseAuth, AuthEnvironmentVariables, AuthApiKey
from cat.mad_hatter.mad_hatter import MadHatter

class AuthorizatorSettings(BaseModel):
    _pyclass: Type[BaseAuth] = None

    @classmethod
    def get_authorizator_from_config(cls, config):
        if cls._pyclass is None or issubclass(cls._pyclass.default, BaseAuth) is False:
            raise Exception(
                "Authorizator configuration class has self._pyclass==None. Should be a valid Authorizator class"
            )
        return cls._pyclass.default(**config)

class AuthEnvironmentVariablesConfig(AuthorizatorSettings):
    _pyclass: Type = AuthEnvironmentVariables

    model_config = ConfigDict(
        json_schema_extra={
            "humanReadableName": "No Authorizator",
            "description": "No authorizator is used. All requests are allowed.",
            "link": "",
        }
    )

class AuthApiKeyConfig(AuthorizatorSettings):
    api_key_http: str
    api_key_ws: str
    _pyclass: Type = AuthApiKey

    model_config = ConfigDict(
        json_schema_extra={
            "humanReadableName": "API Key Authorizator",
            "description": 'Authorize requests based on API key',
            "link": "",
        }
    )

def get_allowed_authorizator_strategies():
    list_authorizator_default = [
        AuthEnvironmentVariablesConfig,
        AuthApiKeyConfig,
    ]

    mad_hatter_instance = MadHatter()
    list_authorizator = mad_hatter_instance.execute_hook(
        "factory_allowed_authorizators", list_authorizator_default, cat=None
    )

    return list_authorizator

def get_authorizators_schemas():
    AUTHORIZATOR_SCHEMAS = {}
    for config_class in get_allowed_authorizator_strategies():
        schema = config_class.model_json_schema()
        schema["auhrizatorName"] = schema["title"]
        AUTHORIZATOR_SCHEMAS[schema["title"]] = schema
    
    return AUTHORIZATOR_SCHEMAS

def get_authorizator_from_name(name):
    list_authorizator = get_allowed_authorizator_strategies()
    for authorizator in list_authorizator:
        if authorizator.__name__ == name:
            return authorizator
    return None