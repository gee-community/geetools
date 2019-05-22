# coding=utf-8
""" User Interface Tools """
import ee
import threading
import pprint
from . import dispatcher

ASYNC = False


def eprint(*args, **kwargs):
    """ Print EE Objects. Similar to `print(object.getInfo())` but with
    some magic (lol)

    :param eeobject: object to print
    :type eeobject: ee.ComputedObject
    :param indent: indentation of the print output
    :type indent: int
    :param do_async: call getInfo() asynchronously
    :type do_async: bool
    """
    indent = kwargs.get('indent', 2)
    do_async = kwargs.get('do_async', ASYNC)
    pp = pprint.PrettyPrinter(indent=indent)

    info_return = [None]*len(args)

    def get_info(eeobject, index):
        """ Get Info """
        info_return[index] = dispatcher.dispatch(eeobject)

    for i, eeobject in enumerate(args):
        # DO THE SAME FOR EVERY OBJECT
        if do_async:
            thread = threading.Thread(target=get_info,
                                      args=(eeobject, i))
            thread.start()
        else:
            get_info(eeobject, i)

    for result in info_return:
        pp.pprint(result)


def getInfo(eeobject):
    """ Get eeobject information (getInfo) asynchronously. For not async just
    use `ee.data.getInfo` """

    class newDict(dict):
        def get(self):
            return self['info']
        def __call__(self):
            return self.get()

    result = newDict({'info':None})

    def get_info(eeobject, from_ee):
        if from_ee:
            info = eeobject.getInfo()
        else:
            info = eeobject

        result['info'] = info

    module = getattr(eeobject, '__module__', None)
    parent = module.split('.')[0] if module else None
    if parent == ee.__name__:
        thread = threading.Thread(target=get_info, args=(eeobject, True))
        thread.start()
    else:
        get_info(eeobject, False)

    return result
