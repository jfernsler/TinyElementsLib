import nuke
import os, shutil, json
import fnmatch

from tinyelements.globals import GLOBAL_DIR, SHOW_DIR, SHOW

def copy_element_to_show(load_info, element):
    """Set up dirs and make copies from the global lib to the show lib for any element
        Also copy the thumbnail because that's good too.

        Arguments:
        load_info (dict) : bunch of info about what's getting copied
        element (string) : Name of the element

        Returns:
        None - but should probably return success
    """
    source_folder = os.path.join(load_info['global_lib'], load_info['category'], element)
    dir_list = os.listdir(source_folder)
    copy_seq_name = get_longest_sequence(dir_list)
    file_list = fnmatch.filter(dir_list, copy_seq_name['name'] + '*')

    target_folder = os.path.join(load_info['show_lib'], load_info['category'], element)

    file_count = len(file_list)

    print('gonna copy:')
    for cf in file_list:
        print('\t%s'%cf)
    print('to %s'%target_folder)

    try:
        progBar = nuke.ProgressTask("Progress job")

        for i, filename in enumerate(file_list):
            if progBar.isCancelled():
                break
            try:
                if os.path.isdir(target_folder) == False:
                    old_umask = os.umask(0)
                    os.makedirs(target_folder, 0o777)
                    os.umask(old_umask)
                progBar.setMessage('Copying file %s : %d of %d'%(filename, i+1, file_count))
                progBar.setProgress(int(i / float(file_count) * 100))

                shutil.copy(os.path.join(source_folder, filename), target_folder)
            except OSError as e:
                message1 = f'had the following error copying {filename}:\n{e}'
                nuke.message(message1)
    except OSError as e:
        message = f'had the following error:\n{e}'
        nuke.message(message)


    try:
        t_global_path = os.path.join(load_info['global_lib'], load_info['category'], '_thumbnails')
        t_show_path = os.path.join(load_info['show_lib'], load_info['category'], '_thumbnails')
        if os.path.isdir(t_show_path) == False:
                        old_umask = os.umask(0)
                        os.makedirs(t_show_path, 0o777)
                        os.umask(old_umask)

        shutil.copy(os.path.join(t_global_path, copy_seq_name['name']+'.gif'), t_show_path)
    except:
        print('had trouble with the thumbnail')


def set_node_attribs(node, element, from_global_lib=True):
    """Set the color and label of a read node based on where it's reading from

        Arguments:
        node (nuke node obj) : The node w/ the data (element read node)
        element (string) : Name of the element
        from_global_lib (bool) : Whether or not its loading from the global lib

        Returns:
        None.
    """
    read_label = element + '\n'
    if from_global_lib:
        read_color = 4278255360
        read_label += 'global lib'
    else:
        read_color = 8494847
        read_label += 'show lib'
    
    node['label'].setValue(read_label)
    node['tile_color'].setValue(read_color)


def load_element_list(load_info):
    """Given a list of element names, load each one, then add nodes as needed to satisfy
        the options

        Arguments:
        load_info (dict) : bunch of info about what to load:
            # load_info['element_list'] = elements_to_load
            # load_info['type'] = self.load_combo.currentText()
            # load_info['category'] = self.category_combo.currentText()
            # load_info['start_frame'] = int(self.frame_field.text())
            # load_info['copy_to'] = self.copy_box.isChecked()
            # load_info['global_lib'] = GLOBAL_DIR
            # load_info['show_lib'] = SHOW_DIR
            # load_info['from_dir'] = self.catalog_combo.currentText()

        Returns:
        None.
    """
    nuke.selectAll()
    nuke.invertSelection()

    position = None
    last_node_list = list()

    library = load_info['global_lib']
    from_global_lib = True


    for element in load_info['element_list']:
        # establish if we need to copy it in:
        if load_info['copy_to']:
            if not os.path.exists(os.path.join(load_info['show_lib'], load_info['category'], element)):
                copy_element_to_show(load_info, element)

        if os.path.exists(os.path.join(load_info['show_lib'], load_info['category'], element)):
            library = load_info['show_lib']
            from_global_lib = False
        
        element_path = os.path.join(library, load_info['category'], element)

        try:
            element_seq = get_img_seq(element_path)
        except:
            print('Something went wrong')
            print('Can not find element at %s'%element_path)
            continue

        element_seq_path = os.path.join(element_path, element_seq['fname'])

        # sort out all the info
        start = element_seq['startframe']
        end = element_seq['endframe']

        # start making stuff
        read = nuke.nodes.Read(file=element_seq_path)
        read['first'].setValue(start)
        read['last'].setValue(end)

        set_node_attribs(read, element, from_global_lib)
        add_data_to_read(read)

        if position is None:
            # center it
            read.setXpos(nuke.center()[0])
            read.setYpos(nuke.center()[1])
        else: 
            # then position each one to the right a bit
            read.setXpos(int(position[0] + 100))
            read.setYpos(int(position[1]))

        position = [read['xpos'].value(), read['ypos'].value()]

        read.setSelected(True)
        last_node = read

        # now apply options
        if 'Centered' in load_info['type']:
            tx_node = make_centering_transform(read)
            tx_node.setSelected(True)
            last_node = tx_node
    
        if start != load_info['start_frame'] and 'Thumb' not in load_info['type']:
            time_o = nuke.createNode('TimeOffset')
            time_o['time_offset'].setValue(load_info['start_frame'] - start)
            time_o.setYpos(time_o.ypos() + 35)
            time_o.setSelected(True)
            last_node = time_o

        last_node_list.append(last_node)

    if 'Switch' in load_info['type']:
        nuke.selectAll()
        nuke.invertSelection()
        x_avg, y_avg = 0,0
        for ln in last_node_list:
            x_avg += ln.xpos()
            y_avg += ln.ypos()
            ln.setSelected(True)
        x = x_avg / len(last_node_list)
        y = y_avg / len(last_node_list) + 200
        switch_node = nuke.createNode('Switch')
        switch_node.setXpos(int(x))
        switch_node.setYpos(int(y))
    
    if 'Thumb' in load_info['type']:
        nuke.selectAll()
        nuke.invertSelection()
        setup_for_thumb(last_node_list)


def setup_for_thumb(node_list):
    """Set up an element to render a thumbnail - still need to run ffmpeg to generate gifs

        Arguments:
        node_list (list of nuke node objs) : elements you want to generate thumbs of

        Returns:
        None.
    """
    for i, node in enumerate(node_list):
        node.setSelected(True)
        node['postage_stamp'].setValue(False)
        filepath = node['file'].value()

        dir = os.path.dirname(filepath)
        name = dir.split('/')[-1]
        
        fname = name + '.mov'
        thumbdir = dir.split('/')[0:-1] + ['_thumbnails']
        thumbdir = '/'.join(thumbdir)
        gname = name + '.gif'
        gifloc = os.path.join(thumbdir, gname)

        thumbdir = os.path.join(thumbdir, 'mov', fname)

        retime = nuke.createNode('Retime')

        retime['output.first_lock'].setValue(True)
        retime['output.last_lock'].setValue(True)
        retime['output.first'].setValue(1)
        retime['output.last'].setValue(20)
        retime['filter'].setValue(1)

        reformat = nuke.createNode('Reformat')
        reformat['type'].setValue(1)
        reformat['box_width'].setValue(256)
        reformat['box_height'].setValue(256)
        reformat['resize'].setValue(3)
        reformat['black_outside'].setValue(True)
        
        writenode = nuke.createNode('Write')
        writenode['create_directories'].setValue(True)
        writenode['file'].setValue(thumbdir)
        writenode['colorspace'].setValue(1)
        writenode['mov64_codec'].setValue('jpeg')

        if os.path.exists(gifloc):
            print(gifloc + ' exists')
            writenode['disable'].setValue(True)


def get_dirs(dir_path):
    """Gets a listing of the directories under one passed to it.
        Ignores certain named directories.

        Arguments:
        dir_path (string) : the path to the directories you're looking for

        Returns:
        list of the contained directory names.
    """
    # get listing and check to make sure it's a dir
    # ignore it if it start with '_'
    ignore_list = ['contactsheet', '_catalogs', 'thumbnails', '_thumbnails']
    try:
        dirs = [ name for name in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, name)) and name not in ignore_list ]
    except FileNotFoundError:
        print('Can not find directory at %s'%dir_path)
        dirs = []
    dirs.sort()
    return dirs


def get_img_seq(dir_path):
    """Get an image sequence from within the sent path.

        Arguments:
        dir_path (string) : the path to the directories you're in

        Returns:
        dictionary of information regarding the image sequence found.
    """
    element_files = os.listdir(dir_path)
    return get_longest_sequence(element_files) 


def get_longest_sequence(dir_list):
    """Finds the longest logical image sequence in a given directory. Looks only
        at a select number of image formats. Finds the pattern of a sequence and
        then returns information regarding only the longest sequence. This way we 
        avoid numbered temp files or partial conversions

        Arguments:
        dir_path (string) : the path to the directories you're looking for

        Returns:
        Dictionary containing:
                info['name'] : base name
                info['count'] : how many images in the seq
                info['startframe'] : start frame
                info['endframe'] : end frame
                info['extension'] : the image file type
                info['frame_format'] : the format of the numbering w/in the seq
                info['fname'] : the sequentially formatted naming

    """
    ext_list = ['.exr', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.hdr']
    dir_list.sort()
    seq_names = set()
    potential_seq = dict()

    for item in dir_list:
        if len(seq_names) > 0 and any(seq in item for seq in seq_names):
            continue
        # see if there are images
        if any(ext in item for ext in ext_list):
            info = dict()
            # clear out the extension
            ext_index = item.rfind('.')
            item_ext = item.split('.')[-1]
            item_name_num = item[0:ext_index]

            # find the seq num
            end_index = len(item_name_num)
            start_index = end_index-1
            found = False
            dot_format = True
            sep = '.'
            num = 'x'
            while not found:
                try:
                    num = int(item_name_num[start_index:end_index])
                    start_index-=1
                    num_pad = end_index-start_index-1

                except:
                    found = True
                    if item_name_num[start_index] != '.':
                        dot_format = False
                        sep = item_name_num[start_index]


            info = dict()
            info['name'] = 'none'
            info['count'] = 0

            if num != 'x':
                info['name'] = item[0:start_index]
                info['count'] = len(fnmatch.filter(dir_list, info['name'] + '*' + item_ext))
                info['startframe'] = num
                info['endframe'] = num + info['count']-1
                info['extension'] = item_ext
                info['frame_format'] = '%0' + str(num_pad) + 'd'
                if dot_format:
                    info['fname'] = '.'.join([info['name'], info['frame_format'], info['extension']])
                else:
                    info['fname'] = info['name'] + sep + info['frame_format'] + '.' + info['extension']
            else:
                #print('un-numbered still')
                info['name'] = item_name_num
                info['count'] = 1
                info['extension'] = item_ext
                info['frame_format'] = 'None'
                info['fname'] = '.'.join([info['name'],info['extension']])

        try:
            potential_seq[info['name']] = info
            seq_names.add(info['name'])
        except:
            print('problem with %s'%item)
            continue

    # print_potential_seq(potential_seq)
    longest = [None, 0]

    for seq in potential_seq.keys():
        if potential_seq[seq]['count'] > longest[1]:
            longest = [seq, potential_seq[seq]['count']]

    return potential_seq[longest[0]]


def print_potential_seq(data):
    for i, d in enumerate(data.keys()):
        print('%d. %s'%(i, d))
        for k in data[d].keys():
            print('\t%s : %s'%(k, data[d][k]))


def add_data_to_read(el_node):
    """Get info about the file and add it to the read node

        Arguments:
        el_node (nuke node obj) : Read node for the element

        Returns:
        None.
    """
    info = dict()
    # Gather data from the read:
    info['start'] = el_node.knob('first').value()
    info['end'] = el_node.knob('last').value()
    info['duration'] = info['end']-info['start']
    info['width'] = el_node.width()
    info['height'] = el_node.height()

    fname = el_node.knob('file').value()
    info['element_dir'] = os.path.dirname(fname)
    info['element_name'] = info['element_dir'].split('/')[-1]

    center = [info['width']/2, info['height']/2]

    # put it in new knobs
    k = nuke.Tab_Knob('Element Info')
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    k = nuke.Text_Knob('Element Name:')
    k.setValue(info['element_name'])
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    k = nuke.Text_Knob('Element Path:')
    k.setValue(info['element_dir'])
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    k = nuke.Text_Knob('Start:')
    k.setValue(str(info['start']))
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    k = nuke.Text_Knob('End:')
    k.setValue(str(info['end']))
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    k = nuke.Text_Knob('Duration:')
    k.setValue(str(info['duration']))
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    k = nuke.Text_Knob('Width:')
    k.setValue(str(info['width']))
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    k = nuke.Text_Knob('Height:')
    k.setValue(str(info['height']))
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    source = nuke.XY_Knob('Source Point')
    source.setValue([info['width']/2, info['height']/2])
    source.setFlag(nuke.STARTLINE)
    el_node.addKnob(source)

    k = nuke.PyScript_Knob('writed', label='Write Data', command='from tinyelements import write_data_json; write_data_json(nuke.thisNode())')
    el_node.addKnob(k)

    k = nuke.PyScript_Knob('make_center', label='Center Source', command='from tinyelements import make_centering_transform; make_centering_transform(nuke.thisNode())')
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    k = nuke.PyScript_Knob('copy_to_show', label='Copy Element to Show', command='from tinyelements import copy_read_to_show; copy_read_to_show(nuke.thisNode())')
    k.setFlag(nuke.STARTLINE)
    el_node.addKnob(k)

    # check for a pre-existing json file, if it's there, apply the centering info
    json_path = os.path.join(info['element_dir'], info['element_name']+'.json')

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            json_data = json.load(json_file)
        info['source_point'] = json_data['source_point']
        apply_offset_anim(source, info['source_point'])
    else:
        info['source_point'] = {0: (info['width']/2, info['height']/2)}

    # open up the first tab again
    el_node['file'].setFlag(0)


def get_center_data(info, center_knob):
    """Look for values on the centering knob of the read, then return it back in the dictionary provided

        Arguments:
        info (dict) : A dictionary we can add info to and return
        center_knob (nuke knob object) : the knob to pull data (animated or still) from

        Returns:
        info (dict) w/ the added data.
    """
    source_dict = dict()
    if center_knob.isAnimated():
        for n in range(info['start'], info['end']+1):
            val = center_knob.getValueAt(n)
            source_dict[n]=val
    else:
        source_dict[0]=center_knob.getValueAt(0)

    info['source_point'] = source_dict
    return info


def write_data_json(node):
    """Write out the json file to ride along-side the element. This primarily provides the 
        centering info as needed, but also gives an opportunity to store things like location,
        resolution, duration, and anything else we may want to store here so we are a bit more
        set for the future of moving this stuff around

        Arguments:
        node (nuke node object) : The read file that has the element data

        Returns:
        None.
    """
    info = gather_data(node)
    data_file = os.path.join(info['element_dir'], info['element_name']+'.json')
    info = get_center_data(info, node.knob('Source Point'))

    with open(data_file, 'w') as f:
        json.dump(info, f, indent=4)
    
    print('data file written to %s'%data_file)


def make_centering_transform(read_node):
    """Make a transform that moves the center to the source, then stabilizes 
        the element in the center of the frame

        Arguments:
        node (nuke node object) : The read file that has the element data

        Returns:
        tx_node (nuke node object) : The created transform.
    """
    ## Check for JSON file
    info = gather_data(read_node)
    info = get_center_data(info, read_node.knob('Source Point'))

    curve_keys = info['source_point'].keys()
    center = [info['width']/2, info['height']/2]

    ypos = read_node.ypos()
    xpos = read_node.xpos()
    tx_node = nuke.createNode('Transform', 'name CenteringTX')
    tx_node['label'].setValue(info['element_name'])
    tx_node.setXpos(xpos)
    tx_node.setYpos(ypos + 100)
    #tx_node.connectInput(0, read_node)
    

    translate_knob = tx_node['translate']
    center_knob = tx_node['center']

    apply_offset_anim(translate_knob, info['source_point'], center)
    apply_offset_anim(center_knob, info['source_point'])

    return tx_node


def apply_offset_anim(anim_knob, anim_dict, center=None):
    """Take anim data {frame : [x, y], ...} and apply it to a knob. If a center is given,
        the anim is subtracted from it for a centered offset

        Arguments:
        anim_knob (nuke knob obj) : right now this needs to be an XY knob as this only works for that
        anim_dict (dict) : anim data formatted as { framenum : [x, y], ...}
        center (float list len 2) : the new center point on the frame [x, y]

        Returns:
        None.
    """
    curve_keys = anim_dict.keys()
    curve_keys.sort()
    if len(curve_keys)>1:
        anim_knob.setAnimated()
    for frame in curve_keys:
        if center is not None:
            x = center[0] - anim_dict[frame][0]
            y = center[1] - anim_dict[frame][1]
        else:
            x = anim_dict[frame][0]
            y = anim_dict[frame][1]
        anim_knob.setValueAt(x, float(frame), 0)
        anim_knob.setValueAt(y, float(frame), 1)


def gather_data(node):
    """Just gathers up the data stored in the node

        Arguments:
        node (nuke node obj) : The node w/ the data (element read node)

        Returns:
        info dictionary.
    """
    info=dict()
    info['element_name'] = node['Element Name:'].value()
    info['element_dir'] = node['Element Path:'].value()
    info['start'] = int(node['Start:'].value())
    info['end'] = int(node['End:'].value())
    info['duration'] = int(node['Duration:'].value())
    info['width'] = int(node['Width:'].value())
    info['height'] = int(node['Height:'].value())
    return info


def copy_read_to_show(node):
    """This is a little embarassing because it's a mess, but hopefully this function won't exist for long.
        Check the file read, if it's global and you want it in the show it will copy the files then alter the 
        read path, change the color of the node, and alter the label.

        Arguments:
        node (nuke node obj) : The node w/ the data (element read node)

        Returns:
        None.
    """
    info = gather_data(node)

    copy_info = dict()
    copy_info['global_lib'] = GLOBAL_DIR
    copy_info['show_lib'] = SHOW_DIR
    copy_info['category'] = info['element_dir'].split('/')[-2]

    show_element_path = os.path.join(copy_info['show_lib'], copy_info['category'], info['element_name'])

    if SHOW not in info['element_dir']:
        copy_element_to_show(copy_info, info['element_name'])
        element_seq = get_img_seq(show_element_path)
        element_seq_path = os.path.join(show_element_path, element_seq['fname'])
        node['file'].setValue(element_seq_path)
        node['Element Path:'].setValue(show_element_path)
        set_node_attribs(node, info['element_name'], from_global_lib=False)


    else:
        print('already copied')
        set_node_attribs(node, info['element_name'], from_global_lib=False)

    