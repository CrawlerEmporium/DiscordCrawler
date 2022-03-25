import utils.globals as GG


def get_name(cogName, command):
    return GG.LOCALIZATION[cogName]['name'][command]['en-US']


def get_description(cogName, command):
    return GG.LOCALIZATION[cogName]['description'][command]['en-US']


def get_names(cogName, command):
    return GG.LOCALIZATION[cogName]['name'][command]


def get_descriptions(cogName, command):
    return GG.LOCALIZATION[cogName]['description'][command]


def get_command_kwargs(cogName, name):
    return{
        "name": get_name(cogName, name),
        "description": get_description(cogName, name),
        "name_localizations": get_names(cogName, name),
        "description_localizations": get_descriptions(cogName, name)
    }


def get_parameter_kwargs(cogName, name):
    return{
        "description": get_description(cogName, name),
        "name_localizations": get_names(cogName, name),
        "description_localizations": get_descriptions(cogName, name)
    }
