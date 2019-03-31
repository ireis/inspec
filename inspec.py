import numpy
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, TextBox
import pyperclip
from astropy.io import fits
from astropy.table import Table

def load_spiders_df(path):

    hdul = fits.open(path)
    data_tbl = Table(hdul[1].data)
    spiders_df = data_tbl.to_pandas()
    spiders_BLAGN_df = spiders_df[ (spiders_df['CLASS_BEST'] == 'BLAGN ') | (spiders_df['CLASS_BEST'] == 'QSO   ')].copy()
    #print(spiders_BLAGN_df.shape)
    #print(spiders_BLAGN_df.head())
    return spiders_BLAGN_df


def get_pmf(plate_mjd_fiber):
    try:
        plate_mjd_fiber = plate_mjd_fiber.values
    except:
        pass
    plate = plate_mjd_fiber[0]
    mjd = plate_mjd_fiber[1]
    fiber = plate_mjd_fiber[2]
    return plate, mjd, fiber

def get_sdss_link(plate_mjd_fiber):
    plate, mjd, fiber = get_pmf(plate_mjd_fiber)
    return 'http://skyserver.sdss.org/dr14/en/tools/explore/summary.aspx?plate={}&mjd={}&fiber={}'.format(plate,mjd,fiber)

class inspec():

    def __init__(self, path_specs, path_wave, path_spider_fits):

        self.specs = numpy.load(path_specs)
        self.wave = numpy.load(path_wave)
        spiders_BLAGN_df = load_spiders_df(path_spider_fits)
        self.n_objects = self.specs.shape[0]



        self.plate_mjd_fiber = spiders_BLAGN_df[['plate', 'MJD', 'fiberID']]




        self.labels = ('Can fit', 'Can fit maybe', 'Complex broad profile',  'No Narrow Hb', 'Do not use')
        self.n_labels = len(self.labels)
        self.ind = 0
        try:
            self.choices = numpy.load('choices.npy')

            for o in range(self.n_objects):
                if numpy.sum(self.choices[o]) > 0:
                    pass
                else:
                    self.ind = o
                    break
        except:
            self.choices = numpy.zeros((self.n_objects, self.n_labels), dtype=int)

        fig, self.ax = plt.subplots(figsize = (10,7))
        plt.subplots_adjust(bottom=0.5)
        self.l, = self.ax.plot(self.wave, numpy.log(1 + self.specs[self.ind]), lw=2)

        plate, mjd, fiber = get_pmf(self.plate_mjd_fiber.iloc[self.ind])
        self.ax.set_title('{}, {}, {}'.format(plate,mjd,fiber))

        sdss_link = get_sdss_link(self.plate_mjd_fiber.iloc[self.ind])
        pyperclip.copy(sdss_link)

        axprev = plt.axes([0.25, 0.2, 0.1, 0.1])
        axnext = plt.axes([0.37, 0.2, 0.1, 0.1])
        self.bnext = Button(axnext, 'Next')
        self.bnext.on_clicked(self.next_obj)

        self.bprev = Button(axprev, 'Previous')
        self.bprev.on_clicked(self.prev_obj)

        self.rax = plt.axes([0.5, 0.05, 0.25, 0.4])
        self.check = CheckButtons(self.rax, self.labels, self.choices[self.ind])
        self.check.on_clicked(self.update)


        self.axtext = plt.axes([0.23, 0.32, 0.25, 0.05])
        self.textbox = TextBox(self.axtext, 'Go to:', str(self.ind))
        self.textbox.on_submit(self.go_to_obj)

        self.xlim = (4600,5100)
        self.ax.set_xlim(self.xlim)

        plt.show()


    def new_obj(self, i):
        self.ax.clear()

        self.l, = self.ax.plot(self.wave, numpy.log(1 + self.specs[i]), lw=2)

        self.ax.set_xlim(self.xlim)
        plate, mjd, fiber = get_pmf(self.plate_mjd_fiber.iloc[i])
        self.ax.set_title('{}, {}, {}'.format(plate,mjd,fiber))
        #self.ax.set_title('')
        #ax.set_title(labels[self.choices[self.ind]])
        self.rax.clear()
        #self.rax = plt.axes([0.1, 0.05, 0.25, 0.2])
        self.check = CheckButtons(self.rax, self.labels, self.choices[self.ind])
        self.check.on_clicked(self.update)

        sdss_link = get_sdss_link(self.plate_mjd_fiber.iloc[i])
        pyperclip.copy(sdss_link)

        self.textbox.set_val(str(i))


    def next_obj(self, event):
        idx = self.ind + 1
        if idx < self.n_objects:
            self.ind = idx
            self.new_obj(self.ind)
        else:
            pass


    def prev_obj(self, event):
        idx = self.ind - 1
        if idx >= 0:
            self.ind = idx
            self.new_obj(self.ind)
        else:
            pass

    def go_to_obj(self, submit):
        idx = eval(submit)
        #i = self.ind % self.n_objects
        if idx < self.n_objects:
            self.ind = idx
            self.new_obj(self.ind)
        else:
            pass


    def update(self, label):
        label_loc = numpy.where([label == l for l in self.labels])[0]
        self.choices[self.ind, label_loc] = not self.choices[self.ind, label_loc]
        numpy.save('choices.npy', self.choices)
