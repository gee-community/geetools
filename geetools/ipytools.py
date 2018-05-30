# coding=utf-8
''' General tools for the Jupyter Notebook and Lab '''

from IPython.display import display
from ipywidgets import HTML, Tab, Text, Accordion, Checkbox, HBox, Output,\
                       DOMWidget, Layout, Widget, Label, VBox, Button,\
                       ToggleButton, IntSlider
from traitlets import HasTraits, List, Unicode, observe, Instance, Tuple, All
import json

# imports for async widgets
import threading
import time

# import EE
import ee
if not ee.data._initialized: ee.Initialize()

def create_accordion(dictionary):
    """ Create an Accordion output from a dict object """
    widlist = []
    ini = 0
    widget = Accordion()
    widget.selected_index = None # this will unselect all
    for key, val in dictionary.items():
        if isinstance(val, dict):
            newwidget = create_accordion(val)
            widlist.append(newwidget)
        elif isinstance(val, list):
            # tranform list to a dictionary
            dictval = {k: v for k, v in enumerate(val)}
            newwidget = create_accordion(dictval)
            widlist.append(newwidget)
        else:
            value = HTML(str(val))
            widlist.append(value)
        widget.set_title(ini, key)
        ini += 1
    widget.children = widlist
    return widget


class CheckRow(HBox):
    checkbox = Instance(Checkbox)
    widget = Instance(Widget)

    def __init__(self, widget, **kwargs):
        self.checkbox = Checkbox(indent=False,
                                layout=Layout(flex='1 1 20', width='auto'))
        self.widget = widget
        super(CheckRow, self).__init__(children=(self.checkbox, self.widget),
                                       **kwargs)
        self.layout = Layout(display='flex', flex_flow='row',
                             align_content='flex-start')

    @observe('widget')
    def _ob_wid(self, change):
        new = change['new']
        self.children = (self.checkbox, new)

    def observe_checkbox(self, handler, extra_params={}, **kwargs):
        """ set handler for the checkbox widget

        :param handler: callback function
        :type handler: function
        :param extra_params: extra parameters that can be passed to the handler
        :type extra_params: dict
        :param kwargs: parameters from traitlets.observe
        :type kwargs: dict
        """
        def proxy_handler(handler):
            def wrap(change):
                change['widget'] = self.widget
                for key, val in extra_params.items():
                    change[key] = val
                return handler(change)
            return wrap
        self.checkbox.observe(proxy_handler(handler), **kwargs)

    def observe_widget(self, handler, extra_params={}, **kwargs):
        """ set handler for the widget alongside de checkbox

        :param handler: callback function
        :type handler: function
        :param extra_params: extra parameters that can be passed to the handler
        :type extra_params: dict
        :param kwargs: parameters from traitlets.observe
        :type kwargs: dict
        """
        def proxy_handler(handler):
            def wrap(change):
                change['checkbox'] = self.checkbox
                for key, val in extra_params.items():
                    change[key] = val
                return handler(change)
            return wrap
        self.widget.observe(proxy_handler(handler), **kwargs)

class CheckAccordion(VBox):
    widgets = Tuple()

    def __init__(self, widgets, **kwargs):
        # self.widgets = widgets
        super(CheckAccordion, self).__init__(**kwargs)
        self.widgets = widgets

    @observe('widgets')
    def _on_child(self, change):
        new = change['new'] # list of any widget
        newwidgets = []
        for widget in new:
            # constract the widget
            acc = Accordion(children=(widget,))
            acc.selected_index = None # this will unselect all
            # create a CheckRow
            checkrow = CheckRow(acc)
            newwidgets.append(checkrow)
        newchildren = tuple(newwidgets)
        self.children = newchildren

    def set_title(self, index, title):
        checkrow = self.children[index]
        acc = checkrow.widget
        acc.set_title(0, title)

    def get_title(self, index):
        checkrow = self.children[index]
        acc = checkrow.widget
        return acc.get_title(0)

    def get_check(self, index):
        ''' get the state of checkbox in index '''
        checkrow = self.children[index]
        return checkrow.checkbox.value

    def set_check(self, index, state):
        ''' set the state of checkbox in index '''
        checkrow = self.children[index]
        checkrow.checkbox.value = state

    def checked_rows(self):
        ''' return a list of indexes of checked rows '''
        checked = []
        for i, checkrow in enumerate(self.children):
            state = checkrow.checkbox.value
            if state: checked.append(i)
        return checked

    def get_widget(self, index):
        ''' get the widget in index '''
        checkrow = self.children[index]
        return checkrow.widget

    def set_widget(self, index, widget):
        ''' set the widget for index '''
        checkrow = self.children[index]
        checkrow.widget.children = (widget,) # Accordion has 1 child

    def set_row(self, index, title, widget):
        ''' set values for the row '''
        self.set_title(index, title)
        self.set_widget(index, widget)

    def set_accordion_handler(self, index, handler, **kwargs):
        ''' set the handler for Accordion in index '''
        checkrow = self.children[index]
        checkrow.observe_widget(handler, names=['selected_index'], **kwargs)

    def set_checkbox_handler(self, index, handler, **kwargs):
        ''' set the handler for CheckBox in index '''
        checkrow = self.children[index]
        checkrow.observe_checkbox(handler, **kwargs)


class AssetManager(CheckAccordion):
    """ Asset Manager Widget """
    def __init__(self, path=None, **kwargs):
        # Get Assets data
        if not path:
            self.path = ee.data.getAssetRoots()[0]['id']
        else:
            self.path = path

        root_list = ee.data.getList({'id': self.path})

        # empty lists to fill with ids, types and widgets
        ids = []
        types = []
        widgets = []
        paths = []

        # first widget (headers)
        first_wid = Label('root folder')
        widgets.append(first_wid)
        types.append('root')
        ids.append(self.path)
        paths.append(self.path)

        # iterate over the list of the root
        for content in root_list:
            # get data
            id = content['id']
            ty = content['type']
            # append data to lists
            paths.append(id)
            ids.append(id.replace(self.path, ''))
            types.append(ty)

            # TODO: change this for a callback that only creates a new AssetManaget when user clicks on asset
            if ty == 'Folder' or ty == 'ImageCollection':
                wid = HTML('')
            else:
                # create widget
                # TODO: Button to get info or load to map
                wid = HTML(ty)
            widgets.append(wid)

        super(AssetManager, self).__init__(widgets=widgets, **kwargs)
        self.widgets = widgets

        # set title of header
        self.set_title(0, self.path)

        # TODO: set handler for title's checkbox: select all checkboxes

        # set titles
        for i, title in enumerate(ids):
            if i == 0: continue
            self.set_title(i, title)

        def handle_new_accordion(change):
            path = change['path']
            index = change['index']
            wid = AssetManager(path)
            self.set_widget(index, wid)

        # set handlers
        for i, path in enumerate(paths):
            self.set_accordion_handler(i, handle_new_accordion,
                                       extra_params={'path':path, 'index':i})

class TaskManager(VBox):
    def __init__(self, **kwargs):
        super(TaskManager, self).__init__(**kwargs)
        # Header
        self.checkbox = Checkbox(indent=False,
                                 layout=Layout(flex='1 1 20', width='auto'))
        self.cancel_selected = Button(description='Cancel Selected',
                                      tooltip='Cancel all selected tasks')
        self.cancel_all = Button(description='Cancell All',
                                 tooltip='Cancel all tasks')
        self.refresh = Button(description='Refresh',
                              tooltip='Refresh Tasks List')
        self.autorefresh = ToggleButton(description='auto-refresh',
                                        tooltip='click to enable/disable autorefresh')
        self.slider = IntSlider(min=1, max=10, step=1, value=5)
        self.hbox = HBox([self.checkbox, self.refresh,
                          self.cancel_selected, self.cancel_all,
                          self.autorefresh, self.slider])

        # Tabs for COMPLETED, FAILED, etc
        self.tabs = Tab()
        # Tabs index
        self.tab_index = {0: 'RUNNING',
                          1: 'COMPLETED',
                          2: 'FAILED',
                          3: 'CANCELED',
                          4: 'UNKNOWN'}

        self.taskVBox = VBox()

        self.runningVBox = VBox()
        self.completedVBox = VBox()
        self.failedVBox = VBox()
        self.canceledVBox = VBox()
        self.unknownVBox = VBox()

        self.tab_widgets_rel = {'RUNNING': self.runningVBox,
                                'COMPLETED': self.completedVBox,
                                'FAILED': self.failedVBox,
                                'CANCELED': self.canceledVBox,
                                'UNKNOWN': self.unknownVBox}

        # Create Tabs
        self.tab_widgets = []
        for key, val in self.tab_index.items():
            widget = self.tab_widgets_rel[val]
            self.tab_widgets.append(widget)
            self.tabs.children = self.tab_widgets
            self.tabs.set_title(key, val)

        ''' autorefresh
        def update_task_list(widget):
            # widget is a VBox
            tasklist = ee.data.getTaskList()
            widlist = []
            for task in tasklist:
                accordion = create_accordion(task)
                if task.has_key('description'):
                    name = '{} ({})'.format(task['description'], task['state'])
                else:
                    name = '{} ({})'.format(task['output_url'][0].split('/')[-1], task['state'])
                mainacc = Accordion(children=(accordion, ))
                mainacc.set_title(0, name)
                mainacc.selected_index = None
                wid = CheckRow(mainacc)
                #wid = CheckRow(accordion)
                widlist.append(wid)
            widget.children = tuple(widlist)

        '''
        def loop(widget):
            while True:
                self.update_task_list()(self.refresh)
                time.sleep(self.slider.value)

        # First widget
        self.update_task_list(vbox=self.runningVBox)(self.refresh)
        # self.children = (self.hbox, self.taskVBox)
        self.children = (self.hbox, self.tabs)

        # Set on_click for refresh button
        self.refresh.on_click(self.update_task_list(vbox=self.selected_tab()))
        ''' autorefresh
        thread = threading.Thread(target=loop, args=(self.taskVBox,))
        thread.start()
        '''
        # Set on_clicks
        self.cancel_all.on_click(self.cancel_all_click)
        self.cancel_selected.on_click(self.cancel_selected_click)
        # self.autorefresh

    def autorefresh_loop(self):
        pass

    def tab_handler(self, change):
        if change['name'] == 'selected_index':
            self.update_task_list()(self.refresh)

    def selected_tab(self):
        index = self.tabs.selected_index
        tab_name = self.tab_index[index]
        return self.tab_widgets_rel[tab_name]

    def update_task_list(self, **kwargs):
        def wrap(button):
            self.selected_tab().children = (HTML('Loading...'),)
            try:
                tasklist = ee.data.getTaskList()
                # empty lists
                running_list = []
                completed_list = []
                failed_list = []
                canceled_list = []
                unknown_list = []
                all_list = {'RUNNING': running_list, 'COMPLETED': completed_list,
                            'FAILED': failed_list, 'CANCELED': canceled_list,
                            'UNKNOWN': unknown_list}
                for task in tasklist:
                    state = task['state']
                    accordion = create_accordion(task)
                    if task['state'] == 'COMPLETED':
                        start = int(task['start_timestamp_ms'])
                        end = int(task['creation_timestamp_ms'])
                        seconds = float((start-end))/1000
                        name = '{} ({} sec)'.format(task['output_url'][0].split('/')[-1],
                                                         seconds)
                    else:
                        name = '{}'.format(task['description'])
                    # Accordion for CheckRow widget
                    mainacc = Accordion(children=(accordion, ))
                    mainacc.set_title(0, name)
                    mainacc.selected_index = None
                    # CheckRow
                    wid = CheckRow(mainacc)
                    # Append widget to the CORRECT list
                    all_list[state].append(wid)
                # Assign Children
                self.runningVBox.children = tuple(running_list)
                self.completedVBox.children = tuple(completed_list)
                self.failedVBox.children = tuple(failed_list)
                self.canceledVBox.children = tuple(canceled_list)
                self.unknownVBox.children = tuple(unknown_list)
            except Exception as e:
                self.selected_tab().children = (HTML(str(e)),)
        return wrap

    def get_selected(self):
        """ Get selected Tasks

        :return: a list of the selected indexes
        """
        selected = []
        children = self.selected_tab().children
        for i, child in enumerate(children):
            # checkrow = child.children[0] # child is an accordion
            state = child.checkbox.value
            if state: selected.append(i)
        return selected

    def get_taskid(self, index):
        # Get selected Tab
        selected_wid = self.selected_tab() # VBox
        # Children of the Tab's VBox
        children = selected_wid.children
        # Get CheckRow that corresponds to the passed index
        checkrow = children[index]
        # Get main accordion
        mainacc = checkrow.widget
        # Get details accordion
        selectedacc = mainacc.children[0]
        for n, child in enumerate(selectedacc.children):
            title = selectedacc.get_title(n)
            if title == 'id':
                return child.value

    def get_selected_taskid(self):
        selected = self.get_selected()
        selected_wid = self.selected_tab() # VBox
        children = selected_wid.children
        taskid_list = []
        for select in selected:
            '''
            checkrow = children[select]
            mainacc = checkrow.widget
            selectedacc = mainacc.children[0]
            for n, child in enumerate(selectedacc.children):
                title = selectedacc.get_title(n)
                if title == 'id':
                    taskid_list.append(child.value)
            '''
            taskid = self.get_taskid(select)
            taskid_list.append(taskid)

        return taskid_list

    def cancel_selected_click(self, button):
        selected = self.get_selected_taskid()
        for taskid in selected:
            try:
                ee.data.cancelTask(taskid)
            except:
                continue
        self.update_task_list()(self.refresh)

    def cancel_all_click(self, button):
        selected_wid = self.selected_tab() # VBox
        children = selected_wid.children
        for n, child in enumerate(children):
            taskid = self.get_taskid(n)
            try:
                ee.data.cancelTask(taskid)
            except:
                continue
        self.update_task_list()(self.refresh)
