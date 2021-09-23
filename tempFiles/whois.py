from datetime import datetime
import discord

from cogsAdmin.models.caseType import CaseType
import utils.globals as GG


async def getMemberEmbed(adminString, guild, noteString, user, warningString):
    await guild.chunk()
    avi = user.avatar.url if user.avatar is not None else None
    roles = sorted(user.roles, key=lambda r: r.position)
    rolenames = ', '.join([r.name for r in roles if r != '@everyone']) or 'None'
    desc = f'{user.name} is currently in {user.status} mode.'
    try:
        member_number = sorted(guild.members, key=lambda m: m.joined_at).index(user) + 1
    except TypeError:
        member_number = "Unknown"
    em = discord.Embed(color=user.color, description=desc, timestamp=datetime.now())
    em.add_field(name='Name', value=user.name),
    em.add_field(name="Display Name", value=user.display_name),
    em.add_field(name='Member Number', value=str(member_number)),
    em.add_field(name='Account Created', value=user.created_at.__format__('%A, %B %d, %Y')),
    em.add_field(name='Join Date', value=user.joined_at.__format__('%A, %B %d, %Y')),
    em.add_field(name='Roles', value=rolenames)
    if noteString != "":
        em.add_field(name='Notes', value=noteString, inline=False)
    if warningString != "":
        em.add_field(name='Warnings', value=warningString, inline=False)
    if adminString != "":
        em.add_field(name='Administration', value=adminString, inline=False)
    em.set_thumbnail(url=avi or None)
    return em


async def getCaseStrings(bans, cases, mutes, notes, tempbans, warnings):
    if cases is not None:
        for x in cases['caseIds']:
            case = await GG.MDB.cases.find_one({"caseId": x})
            if case is not None:
                if case['caseType'] == CaseType.NOTE:
                    notes.append(case)
                elif case['caseType'] == CaseType.WARNING:
                    warnings.append(case)
                elif case['caseType'] == CaseType.MUTE:
                    mutes.append(case)
                elif case['caseType'] == CaseType.TEMPBAN:
                    tempbans.append(case)
                elif case['caseType'] == CaseType.BAN:
                    bans.append(case)
    warningString = ""
    if len(warnings) > 0:
        for note in warnings:
            warningString += f"{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    adminString = ""
    if len(mutes) > 0:
        for note in mutes:
            adminString += f"[**MUTED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    if len(tempbans) > 0:
        for note in tempbans:
            adminString += f"[**TEMP-BANNED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    if len(bans) > 0:
        for note in bans:
            adminString += f"[**BANNED**]\n{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    noteString = ""
    if len(notes) > 0:
        for note in notes:
            noteString += f"{note['message']}\n(Id: ``{note['caseId']}`` - {note['date'].__format__('%B %d, %Y')})\n\n"
    return adminString, noteString, warningString
