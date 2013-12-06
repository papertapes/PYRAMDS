"""
PYRAMDS (Python for Radioisotope Analysis & Multidetector Suppression)

Data parser for PIXIE List Mode binary data *.bin
The data contained in the .bin file is reformatted into an HDF5 file
that stores event information is a series of related table entries for quick
extraction of the necessary events used in spectra construction.

"""
import os
from datetime import datetime
from fnmatch import fnmatch
from os.path import basename, dirname, join

from tables import Float32Col, Int32Col, IsDescription
from traits.api import Button, File, HasTraits, Instance, Int, Property, Str, List
from traitsui.api import Group, VGroup, HSplit, Item, View, ListStrEditor, FileEditor

# Setup PyTables metaclasses for use in Table constructor
class GammaEvent(IsDescription):

    # Energy reading from Pixie detector channels 0, 1, 2
    energy_0  = Int32Col(pos=0)
    energy_1  = Int32Col(pos=1)
    energy_2  = Int32Col(pos=2)

    # Time differences between detector events
    # (e.g. "deltaT_01" is between energy_0 and energy_1)
    deltaT_01 = Float32Col(pos=3)
    deltaT_02 = Float32Col(pos=4)
    deltaT_12 = Float32Col(pos=5)

    timestamp = Float32Col(pos=6)

class AggEvent1(IsDescription):
    energy    = Int32Col(pos=0)
    timestamp = Float32Col(pos=1)

class AggEvent2(IsDescription):
    energy_1  = Int32Col(pos=0)
    energy_2  = Int32Col(pos=1)
    timestamp = Float32Col(pos=2)

class PyramdsParser(HasTraits):

    # Path to data file selected in UI
    selected_data_file = File()

    # Path to current working directory
    data_cwd = Property

    # File series base name (series number and extension removed)
    series_basename = Property

    # List containing all files in data series
    file_series = List()

    # Filecounter that tracks progress through file series
    file_counter = Int(1)

    # File path currently being processed (no extension)
    active_file_path = Property

    # Only initialize buffer counter before the entire run
    buffer_no = 0

    def get_file_series(self, ext):

        self.file_series = []

        # Populate file_series list
        file_wildcard = self.series_basename + '*.' + ext

        for file in os.listdir(self.data_cwd):
            if fnmatch(join(self.data_cwd, file), file_wildcard):
                self.file_series.append(file)
        return self.file_series

    def get_bin_info(self):

        active_file_ifm = self.active_file_path + ".ifm"

        with open(active_file_ifm, 'rU') as finfo:

            info_str_list = finfo.readlines()

            date_str = info_str_list[1][23:-2]
            date_format = '%I:%M:%S %p %a, %b %d, %Y'
            run_start_time = datetime.strptime(date_str, date_format)

            # Total time = real time
            total_time = info_str_list[6].split()[3]

            # Live time for each detector channel
            live_time = [info_str_list[9 + channel].split()[2] for channel in range(4)]

            self.times = {
                'start' :   run_start_time,
                'total' :   total_time,
                'live'  :   live_time
            }

            self.bufheadlen = int(info_str_list[33].split()[1])
            self.eventheadlen = int(info_str_list[34].split()[1])

            # Due to bug in PIXIE IGOR Software, explicity set head length
            self.chanheadlen = 2 #int(info_str_list[35].split()[1])


    def _get_data_cwd(self):
        return dirname(parser.series_basename)

    def _get_series_basename(self):
        return self.selected_data_file[:-8]

    def _get_active_file_path(self):
        return "{self.series_basename}{self.file_counter:0>4}".format(self=self)

class PyramdsView(HasTraits):
    Parser = Instance(PyramdsParser)

    bin_file_editor = FileEditor(filter=['*.bin'])
    hdf_file_editor = FileEditor(filter=['*.h5'])
    series_editor = ListStrEditor(editable=False)

    bin_filename = File()
    hdf_filename = File()
    file_series = List()
    parse_button = Button(label="Parse Series")

    traits_view = View(
        Group(
            VGroup(Item('bin_filename', editor=bin_file_editor, label='BIN File'),
                   HSplit(Item('file_series', editor=series_editor, label='Series',width=0.4),
                          Item('file_series', editor=series_editor, label='Stats'),
                          springy=True),
            show_border=True),
            VGroup(Item('parse_button', show_label=False)),
            label="PIXE PARSER"),
        Group(
            VGroup(Item('hdf_filename', editor=bin_file_editor, label='HDF File'),
            show_border=True,),label="SPECTRUM EXPORTER"),
        resizable = True,
        title = "PYRAMDS",
        )

    # On filename change, update parser model and pull new .ifm stats
    def _bin_filename_changed(self, new):
       
       self.Parser.selected_data_file = new
       self.file_series = self.Parser.get_file_series('bin')
       
       for ifm in self.Parser.get_file_series('ifm'):
           pass

if __name__ == '__main__':
    parser = PyramdsParser()

    PyramdsWindow = PyramdsView(Parser=parser)
    PyramdsWindow.configure_traits()
