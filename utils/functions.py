import utils.globals as GG


def get_name(cogName):
    return GG.LOCALIZATION[cogName]['name']['en-US']


def get_description(cogName):
    return GG.LOCALIZATION[cogName]['description']['en-US']


def get_names(cogName, command):
    return GG.LOCALIZATION[cogName]['name'][command]


def get_descriptions(cogName, command):
    return GG.LOCALIZATION[cogName]['description'][command]
