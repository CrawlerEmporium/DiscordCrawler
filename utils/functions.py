import logging
import utils.globals as GG

log = logging.getLogger(__name__)


class SearchException(Exception):
    pass


async def get_next_case_num():
    reportNum = await GG.MDB['properties'].find_one({'key': 'caseId'})
    num = reportNum['amount'] + 1
    reportNum['amount'] += 1
    await GG.MDB['properties'].replace_one({"key": 'caseId'}, reportNum)
    return num
