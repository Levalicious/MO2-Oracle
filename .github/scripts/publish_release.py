#!/bin/python
from dataclasses import dataclass
import json
from datetime import date
import os

def uget(var: str) -> str:
    val = os.environ.get(var)
    if val is None:
        print(f'{val}')
        print(f'{os.environ}')
        raise ValueError(f'{var} cannot be None')
    return val
    
@dataclass
class PluginVersion:
    Version: str
    Released: str
    MinSupport: str
    MaxSupport: str
    MinWorking: str
    MaxWorking: str
    DownloadUrl: str
    PluginPath: list[str]
    LocalePath: list[str]
    DataPath: list[str]
    ReleaseNotes: list[str]

class PluginDefinition:
    def __init__(self, path: str) -> None:
        with open(path, encoding='utf-8', mode='r') as f:
            data = json.load(f) # pyright: ignore[reportAny]
        self.Name: str = data['Name']
        self.Author: str = data['Author']
        self.Description: str = data['Description']
        self.DocsUrl: str = data['DocsUrl']
        self.GithubUrl: str = data['GithubUrl']
        self.NexusUrl: str = data['NexusUrl']
        self.Versions: list[PluginVersion] = [PluginVersion(**v) for v in data['Versions']] # pyright: ignore[reportAny]
    
    def save(self, path: str) -> None:
        vers: list[PluginVersion] = self.Versions
        self.Versions = [vars(v) for v in self.Versions] # pyright: ignore[reportAttributeAccessIssue]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({**vars(self)}, f, indent=4)
        self.Versions = vers

version = uget('VERSION')
min_support = uget('MIN_SUPPORT')
max_support = uget('MAX_SUPPORT')
plugin_name = uget('PLUGINNAME')
plugin_path = uget('PLUGINPATH')
repo = uget('GITHUB_REPOSITORY')

download_url = f'https://github.com/{repo}/releases/download/v{version}/{plugin_name}-{version}.zip'
definition_path = 'plugin_definition.json'
today = date.today().isoformat()

plugin = PluginDefinition(definition_path)
versions = set(v.Version for v in plugin.Versions)

if version in versions:
    print(f'Version {version} already present in plugin_definition.json')
    exit(1)

plugin.Versions.append(PluginVersion(Version=version, Released=today, 
                                    MinSupport=min_support, MaxSupport=max_support, 
                                    MinWorking=min_support, MaxWorking=max_support, 
                                    DownloadUrl=download_url, PluginPath=[plugin_name], 
                                    LocalePath=[], DataPath=[plugin_path], 
                                    ReleaseNotes=[]))

plugin.save(definition_path)