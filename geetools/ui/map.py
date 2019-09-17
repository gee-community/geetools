# coding=utf-8
""" Basic Map tools """

import ee


def formatVisParams(visParams):
    """ format visualization params to match getMapId requirement """
    copy = {key: val for key, val in visParams.items()}

    def list2str(params):
        n = len(params)
        if n == 3:
            newbands = '{},{},{}'.format(params[0], params[1], params[2])
        else:
            newbands = '{}'.format(params[0])
        return newbands

    if 'bands' in copy:
        copy['bands'] = list2str(copy['bands'])

    if 'palette' in copy:
        if isinstance(copy['palette'], list):
            copy['palette'] = ','.join(copy['palette'])
        else:
            copy['palette'] = [str(copy['palette'])]

    for k in ['min', 'max', 'bias', 'gain', 'gamma']:
        if k in copy:
            if isinstance(copy[k], list):
                copy[k] = list2str(copy[k])
            else:
                value = float(copy[k])
                copy[k] = [value, value, value]

    return copy

