# coding=utf-8
""" User Interface Tools """
import ee
import threading
import pprint
from . import chart, imagestrip, ipymap, ipytools, maptool, dispatcher

from IPython.display import display
from ipywidgets import Output, HTML, VBox, Widget, Label, Accordion


NOTEBOOK = False
ASYNC = False


def eprint(*args, **kwargs):
    """ Print EE Objects. Similar to `print(object.getInfo())` but with
    some magic (lol)

    :param eeobject: object to print
    :type eeobject: ee.ComputedObject
    :param notebook: if True, prints the object as an Accordion Widget for
    the Jupyter Notebook
    :type notebook: bool
    :param indent: indentation of the print output
    :type indent: int
    :param do_async: call getInfo() asynchronously
    :type do_async: bool
    """
    indent = kwargs.get('indent', 2)
    notebook = kwargs.get('notebook', NOTEBOOK)
    do_async = kwargs.get('do_async', ASYNC)
    pp = pprint.PrettyPrinter(indent=indent)

    # VERTICAL GRID WIDGET TO OUTPUT RESULTS
    infowin = VBox([Output()]*len(args))

    # HELPER
    def setchildren(vbox, i, val):
        children = list(vbox.children)
        children[i] = val
        vbox.children = children

    if do_async and not notebook:
        print('Cannot make async printing outside a Jupyter environment')
        do_async = False

    info_return = [None]*len(args)

    def get_info(eeobject, index):
        """ Get Info """
        if notebook:
            widget = dispatcher.widgetDispatcher(eeobject)
            setchildren(infowin, index, widget)
        else:
            info_return[index] = dispatcher.eeobjectDispatcher(eeobject)

    for i, eeobject in enumerate(args):
        # DO THE SAME FOR EVERY OBJECT
        if do_async:
            thread = threading.Thread(target=get_info,
                                      args=(eeobject, i))
            thread.start()
        else:
            get_info(eeobject, i)

    if notebook:
        display(infowin)
    else:
        for result in info_return:
            pp.pprint(result)
            print('')


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

try:
    from .ipymap import Map
    from .ipytools import TaskManager, AssetManager
except ImportError:
    pass
