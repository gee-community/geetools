# coding=utf-8
""" General tools for the Jupyter Notebook and Lab """

from ipywidgets import HTML, Tab, Accordion, Checkbox, HBox, Layout, Widget, \
    VBox, Button, Box, ToggleButton, IntSlider, FloatText
from traitlets import List, Unicode, observe, Instance, Tuple, Int, Float

from .. import batch

# imports for async widgets
from threading import Thread
from multiprocessing import Pool
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


def create_object_output(object):
    ''' Create a output Widget for Images, Geometries and Features '''

    ty = object.__class__.__name__

    if ty == 'Image':
        info = object.getInfo()
        image_id = info['id'] if 'id' in info else 'No Image ID'
        prop = info.get('properties')
        bands = info.get('bands')
        bands_names = [band.get('id') for band in bands]

        # BAND PRECISION
        bands_precision = []
        for band in bands:
            data = band.get('data_type')
            if data:
                precision = data.get('precision')
                bands_precision.append(precision)

        # BAND CRS
        bands_crs = []
        for band in bands:
            crs = band.get('crs')
            bands_crs.append(crs)

        # BAND MIN AND MAX
        bands_min = []
        for band in bands:
            data = band.get('data_type')
            if data:
                bmin = data.get('min')
                bands_min.append(bmin)

        bands_max = []
        for band in bands:
            data = band.get('data_type')
            if data:
                bmax = data.get('max')
                bands_max.append(bmax)

        # BANDS
        new_band_names = []
        zipped_data = zip(bands_names, bands_precision, bands_min, bands_max,
                          bands_crs)
        for name, ty, mn, mx, epsg in zipped_data:
            value = '<li><b>{}</b> ({}) {} to {} - {}</li>'.format(name,ty,
                                                                   mn,mx,epsg)
            new_band_names.append(value)
        bands_wid = HTML('<ul>'+''.join(new_band_names)+'</ul>')

        # PROPERTIES
        if prop:
            new_properties = []
            for key, val in prop.items():
                value = '<li><b>{}</b>: {}</li>'.format(key, val)
                new_properties.append(value)
            prop_wid = HTML('<ul>'+''.join(new_properties)+'</ul>')
        else:
            prop_wid = HTML('Image has no properties')

        # ID
        header = HTML('<b>Image id:</b> {id} </br>'.format(id=image_id))

        acc = Accordion([bands_wid, prop_wid])
        acc.set_title(0, 'Bands')
        acc.set_title(1, 'Properties')
        acc.selected_index = None # thisp will unselect all

        return VBox([header, acc])
    elif ty == 'FeatureCollection':
        try:
            info = object.getInfo()
        except:
            print('FeatureCollection limited to 4000 features')
            info = object.limit(4000)

        return create_accordion(info)
    else:
        info = object.getInfo()
        return create_accordion(info)


def create_async_output(object, widget):
    try:
        child = create_object_output(object)
    except Exception as e:
        child = HTML('There has been an error: {}'.format(str(e)))

    widget.children = [child]


# def recrusive_delete_asset_to_widget(assetId, widget):
def recrusive_delete_asset_to_widget(args):
    ''' adapted version to print streaming results in a widget '''
    assetId = args[0]
    widget = args[1]
    try:
        content = ee.data.getList({'id':assetId})
    except Exception as e:
        widget.value = str(e)
        return

    if content == 0:
        # delete empty colletion and/or folder
        ee.data.deleteAsset(assetId)
    else:
        for asset in content:
            path = asset['id']
            ty = asset['type']
            if ty == 'Image':
                ee.data.deleteAsset(path)
                widget.value += 'deleting {} ({})</br>'.format(path, ty)
            else:
                # clear output
                widget.value = ''
                recrusive_delete_asset_to_widget(path, widget)
        # delete empty colletion and/or folder
        ee.data.deleteAsset(assetId)


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
        """ set handler for the checkbox widget. Use the property 'widget' of
        change to get the corresponding widget

        :param handler: callback function
        :type handler: function
        :param extra_params: extra parameters that can be passed to the handler
        :type extra_params: dict
        :param kwargs: parameters from traitlets.observe
        :type kwargs: dict
        """
        # by default only observe value
        name = kwargs.get('names', 'value')

        def proxy_handler(handler):
            def wrap(change):
                change['widget'] = self.widget
                for key, val in extra_params.items():
                    change[key] = val
                return handler(change)
            return wrap
        self.checkbox.observe(proxy_handler(handler), names=name, **kwargs)

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
        ''' set the title of the widget at indicated index'''
        checkrow = self.children[index]
        acc = checkrow.widget
        acc.set_title(0, title)

    def get_title(self, index):
        ''' get the title of the widget at indicated index'''
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


class AssetManager(VBox):
    """ Asset Manager Widget """
    POOL_SIZE = 5

    def __init__(self, map=None, **kwargs):
        super(AssetManager, self).__init__(**kwargs)
        # Thumb height
        self.thumb_height = kwargs.get('thumb_height', 300)
        self.root_path = ee.data.getAssetRoots()[0]['id']

        # Map
        self.map = map

        # Header
        self.reload_button = Button(description='Reload')
        self.add2map = Button(description='Add to Map')
        self.delete = Button(description='Delete Selected')
        header_children = [self.reload_button, self.delete]

        # Add2map only if a Map has been passed
        if self.map:
            header_children.append(self.add2map)

        self.header = HBox(header_children)

        # Reload handler
        def reload_handler(button):
            new_accordion = self.core(self.root_path)
            # Set VBox children
            self.children = [self.header, new_accordion]

        # add2map handler
        def add2map_handler(themap):
            def wrap(button):
                selected_rows = self.get_selected()
                for asset, ty in selected_rows.items():
                    if ty == 'Image':
                        im = ee.Image(asset)
                        themap.addLayer(im, {}, asset)
                    elif ty == 'ImageCollection':
                        col = ee.ImageCollection(asset)
                        themap.addLayer(col)
            return wrap

        # Set reload handler
        # self.reload_button.on_click(reload_handler)
        self.reload_button.on_click(self.reload)

        # Set reload handler
        self.add2map.on_click(add2map_handler(self.map))

        # Set delete selected handler
        self.delete.on_click(self.delete_selected)

        # First Accordion
        self.root_acc = self.core(self.root_path)

        # Set VBox children
        self.children = [self.header, self.root_acc]

    def delete_selected(self, button=None):
        ''' function to delete selected assets '''
        selected = self.get_selected()

        # Output widget
        output = HTML('')

        def handle_yes(button):
            self.children = [self.header, output]
            # pool = pp.ProcessPool(self.POOL_SIZE)
            if selected:
                assets = [ass for ass in selected.keys()]
                ''' OLD
                for asset, ty in selected.items():
                    recrusive_delete_asset_to_widget(asset, output)
                
                args = []
                for asset, ty in selected.items():
                    args.append((asset, output))

                # pool.map(recrusive_delete_asset_to_widget, args)
                # pool.map(test2, args)
                # pool.close()
                # pool.join()
                '''
                ''' Pool way (not good)
                pool = Pool(self.POOL_SIZE)
                pool.map(batch.recrusive_delete_asset, assets)
                # TODO: cant map recrusive_delete_asset_to_widget because the passed widget is not pickable
                pool.close()
                pool.join()
                '''
                for assetid in assets:
                    thread = Thread(target=batch.recrusive_delete_asset,
                                    args=(assetid,))
                    thread.start()

            # when deleting end, reload
            self.reload()

        def handle_no(button):
            self.reload()
        def handle_cancel(button):
            self.reload()

        assets_str = ['{} ({})'.format(ass, ty) for ass, ty in selected.items()]
        assets_str = '</br>'.join(assets_str)
        confirm = ConfirmationWidget('<h2>Delete {} assets</h2>'.format(len(selected.keys())),
                                     'The following assets are going to be deleted: </br> {} </br> Are you sure?'.format(assets_str),
                                     handle_yes=handle_yes,
                                     handle_no=handle_no,
                                     handle_cancel=handle_cancel)

        self.children = [self.header, confirm, output]

    def reload(self, button=None):
        new_accordion = self.core(self.root_path)
        # Set VBox children
        self.children = [self.header, new_accordion]

    def get_selected(self):
        ''' get the selected assets

        :return: a dictionary with the type as key and asset root as value
        :rtype: dict
        '''
        def wrap(checkacc, assets={}, root=self.root_path):
            children = checkacc.children # list of CheckRow
            for child in children:
                checkbox = child.children[0] # checkbox of the CheckRow
                widget = child.children[1] # widget of the CheckRow (Accordion)
                state = checkbox.value

                if isinstance(widget.children[0], CheckAccordion):
                    title = widget.get_title(0).split(' ')[0]
                    new_root = '{}/{}'.format(root, title)
                    newselection = wrap(widget.children[0], assets, new_root)
                    assets = newselection
                else:
                    if state:
                        title = child.children[1].get_title(0)
                        # remove type that is between ()
                        ass = title.split(' ')[0]
                        ty = title.split(' ')[1][1:-1]
                        # append root
                        ass = '{}/{}'.format(root, ass)
                        # append title to selected list
                        # assets.append(title)
                        assets[ass] = ty

            return assets

        # get selection on root
        begin = self.children[1]  # CheckAccordion of root
        return wrap(begin)

    def core(self, path):
        # Get Assets data

        root_list = ee.data.getList({'id': path})

        # empty lists to fill with ids, types, widgets and paths
        ids = []
        types = []
        widgets = []
        paths = []

        # iterate over the list of the root
        for content in root_list:
            # get data
            id = content['id']
            ty = content['type']
            # append data to lists
            paths.append(id)
            ids.append(id.replace(path+'/', ''))
            types.append(ty)
            wid = HTML('Loading..')
            widgets.append(wid)

        # super(AssetManager, self).__init__(widgets=widgets, **kwargs)
        # self.widgets = widgets
        asset_acc = CheckAccordion(widgets=widgets)

        # TODO: set handler for title's checkbox: select all checkboxes (DONE)

        # set titles
        for i, (title, ty) in enumerate(zip(ids, types)):
            final_title = '{title} ({type})'.format(title=title, type=ty)
            asset_acc.set_title(i, final_title)

        def handle_new_accordion(change):
            path = change['path']
            index = change['index']
            ty = change['type']
            if ty == 'Folder' or ty == 'ImageCollection':
                wid = self.core(path)
            else:
                image = ee.Image(path)
                try:
                    info = image.getInfo()
                    width = int(info['bands'][0]['dimensions'][0])
                    height = int(info['bands'][0]['dimensions'][1])

                    new_width = int(self.thumb_height/height*width)

                    thumb = image.getThumbURL({'dimensions':[new_width,
                                                             self.thumb_height]})
                    # wid = ImageWid(value=thumb)
                    wid_i = HTML('<img src={}>'.format(thumb))
                    wid_info = create_accordion(info)
                    wid = HBox(children=[wid_i, wid_info])
                except Exception as e:
                    message = str(e)
                    wid = HTML(message)

            asset_acc.set_widget(index, wid)

        def handle_checkbox(change):
            path = change['path']
            widget = change['widget'] # Accordion
            wid_children = widget.children[0]  # can be a HTML or CheckAccordion
            new = change['new']

            if isinstance(wid_children, CheckAccordion): # set all checkboxes to True
                for child in wid_children.children:
                    check = child.children[0]
                    check.value = new

        # set handlers
        for i, (path, ty) in enumerate(zip(paths, types)):
            asset_acc.set_accordion_handler(
                i, handle_new_accordion,
                extra_params={'path':path, 'index':i, 'type': ty}
            )
            asset_acc.set_checkbox_handler(
                i, handle_checkbox,
                extra_params={'path':path, 'index':i, 'type': ty}
            )

        return asset_acc


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
        ''' get the selected tab '''
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


class ConfirmationWidget(VBox):
    def __init__(self, title='Confirmation', legend='Are you sure?',
                 handle_yes=None, handle_no=None, handle_cancel=None, **kwargs):
        super(ConfirmationWidget, self).__init__(**kwargs)
        # Title Widget
        self.title = title
        self.title_widget = HTML(self.title)
        # Legend Widget
        self.legend = legend
        self.legend_widget = HTML(self.legend)
        # Buttons
        self.yes = Button(description='Yes')
        handler_yes = handle_yes if handle_yes else lambda x: x
        self.yes.on_click(handler_yes)

        self.no = Button(description='No')
        handler_no = handle_no if handle_no else lambda x: x
        self.no.on_click(handler_no)

        self.cancel = Button(description='Cancel')
        handler_cancel = handle_cancel if handle_cancel else lambda x: x
        self.cancel.on_click(handler_cancel)

        self.buttons = HBox([self.yes, self.no, self.cancel])

        self.children = [self.title_widget, self.legend_widget, self.buttons]


class RealBox(Box):
    """ Real Box Layout

    items:
    [[widget1, widget2],
     [widget3, widget4]]

    """
    items = List()
    width = Int()
    border_inside = Unicode()
    border_outside = Unicode()

    def __init__(self, **kwargs):
        super(RealBox, self).__init__(**kwargs)

        self.layout = Layout(display='flex', flex_flow='column',
                             border=self.border_outside)

    def max_row_elements(self):
        maxn = 0
        for el in self.items:
            n = len(el)
            if n>maxn:
                maxn = n
        return maxn

    @observe('items')
    def _ob_items(self, change):
        layout_columns = Layout(display='flex', flex_flow='row')
        new = change['new']
        children = []
        # recompute size
        maxn = self.max_row_elements()
        width = 100/maxn
        for el in new:
            for wid in el:
                if not wid.layout.width:
                    if self.width:
                        wid.layout = Layout(width='{}px'.format(self.width),
                                            border=self.border_inside)
                    else:
                        wid.layout = Layout(width='{}%'.format(width),
                                            border=self.border_inside)
            hbox = Box(el, layout=layout_columns)
            children.append(hbox)
        self.children = children


class FloatBandWidget(HBox):
    min = Float(0)
    max = Float(1)

    def __init__(self, **kwargs):
        super(FloatBandWidget, self).__init__(**kwargs)
        self.minWid = FloatText(value=self.min, description='min')
        self.maxWid = FloatText(value=self.max, description='max')

        self.children = [self.minWid, self.maxWid]

        self.observe(self._ob_min, names=['min'])
        self.observe(self._ob_max, names=['max'])

    def _ob_min(self, change):
        new = change['new']
        self.minWid.value = new

    def _ob_max(self, change):
        new = change['new']
        self.maxWid.value = new