import numpy
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
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

    def __init__(self, run_name, path_spider_fits):

        self.run_name = run_name
        if not self.run_name == 'all_objects':
            self.objects_inds = numpy.load('{}.npy'.format(run_name))
        else:
            self.choices = numpy.load('choices_fits.npy')
            self.objects_inds = numpy.where(self.choices.sum(axis=1) == 0)[0]

        spiders_BLAGN_df = load_spiders_df(path_spider_fits)
        self.n_objects = spiders_BLAGN_df.shape[0]
        self.plate_mjd_fiber = spiders_BLAGN_df[['plate', 'MJD', 'fiberID']]

        self.labels = ('Good fit', 'Bad fit', 'No narrow Hb')
        self.n_labels = len(self.labels)
        self.i = 0
        self.ind = self.objects_inds[self.i]
        try:
            self.choices = numpy.load('choices_fits.npy')

            for o in self.objects_inds:
                if numpy.sum(self.choices[o]) > 0:
                    pass
                else:
                    self.ind = o
                    break
        except:
            self.choices = numpy.zeros((self.n_objects, self.n_labels), dtype=int)

        fig, self.ax = plt.subplots(figsize = (10,7))
        plt.subplots_adjust(bottom=0.41)
        figure_file_name = "fit_results/figures/finalfit_{}_idx_{}.png".format(self.run_name,self.ind)
        try:
            img=mpimg.imread(figure_file_name)
            self.ax.imshow(img, aspect='auto')
        except:
            pass

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

        self.rax = plt.axes([0.5, 0.05, 0.25, 0.3])
        if numpy.sum(self.choices[self.ind]) == 0:
            self.check = CheckButtons(self.rax, self.labels, (0,1,0))
        else:
            self.check = CheckButtons(self.rax, self.labels, self.choices[self.ind])
        self.check.on_clicked(self.update)


        self.axtext = plt.axes([0.23, 0.32, 0.25, 0.05])
        self.textbox = TextBox(self.axtext, 'Go to:', str(self.ind))
        self.textbox.on_submit(self.go_to_obj)



        plt.show()


    def new_obj(self, i):
        self.ax.clear()

        figure_file_name = "fit_results/figures/finalfit_{}_idx_{}.png".format(self.run_name,self.ind)
        try:
            img=mpimg.imread(figure_file_name)
            self.ax.imshow(img, aspect='auto')
        except:
            pass
        plate, mjd, fiber = get_pmf(self.plate_mjd_fiber.iloc[i])
        self.ax.set_title('{}, {}, {}'.format(plate,mjd,fiber))
        #self.ax.set_title('')
        #ax.set_title(labels[self.choices[self.ind]])
        self.rax.clear()
        #self.rax = plt.axes([0.1, 0.05, 0.25, 0.2])
        if numpy.sum(self.choices[self.ind]) == 0:
            self.check = CheckButtons(self.rax, self.labels, (0,1,0))
        else:
            self.check = CheckButtons(self.rax, self.labels, self.choices[self.ind])

        self.check.on_clicked(self.update)

        sdss_link = get_sdss_link(self.plate_mjd_fiber.iloc[i])
        pyperclip.copy(sdss_link)

        self.textbox.set_val(str(i))


    def next_obj(self, event):

        self.choices[self.ind, :] = self.check.get_status()
        numpy.save('choices_fits.npy', self.choices)

        idx = self.i + 1
        if idx < self.n_objects:
            self.i = idx
            self.ind = self.objects_inds[self.i]
            self.new_obj(self.ind)
        else:
            pass


    def prev_obj(self, event):

        self.choices[self.ind, :] = self.check.get_status()
        numpy.save('choices_fits.npy', self.choices)


        idx = self.i - 1
        if idx >= 0:
            self.i = idx
            self.ind = self.objects_inds[self.i]
            self.new_obj(self.ind)
        else:
            pass

    def go_to_obj(self, submit):

        self.choices[self.ind, :] = self.check.get_status()
        numpy.save('choices_fits.npy', self.choices)

        idx = eval(submit)
        #i = self.ind % self.n_objects
        if idx in self.objects_inds:
            self.i = numpy.where(idx == self.objects_inds)[0][0]
            self.ind = self.objects_inds[self.i]
            self.new_obj(self.ind)
        else:
            pass


    def update(self, label):
        label_loc = numpy.where([label == l for l in self.labels])[0]
        self.choices[self.ind, label_loc] = not self.choices[self.ind, label_loc]
        numpy.save('choices_fits.npy', self.choices)
