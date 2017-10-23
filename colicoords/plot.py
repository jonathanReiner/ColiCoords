import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import seaborn.timeseries
from colicoords.config import cfg
import seaborn as sns
sns.set_style('white')



# #todo add src, python 2
# def _plot_std_bars(*args, central_data=None, ci=None, data=None, **kwargs):
#     std = data.std(axis=0)
#     ci = np.asarray((central_data - std, central_data + std))
#     kwargs.update({"central_data": central_data, "ci": ci, "data": data})
#     seaborn.timeseries._plot_ci_bars(*args, **kwargs)


# https://stackoverflow.com/questions/34293687/standard-deviation-and-errors-bars-in-seaborn-tsplot-function-in-python
def _plot_std_bars(*args, **kwargs):
    data = kwargs.pop('data')
    central_data = kwargs.pop('central_data')
    kwargs.pop('ci')

    std = data.std(axis=0)
    ci = np.asarray((central_data - std, central_data + std))
    kwargs.update({"central_data": central_data, "ci": ci, "data": data})
    seaborn.timeseries._plot_ci_bars(*args, **kwargs)


def _plot_std_band(*args, **kwargs):
    data = kwargs.pop('data')
    central_data = kwargs.pop('central_data')
    kwargs.pop('ci')

    std = data.std(axis=0)
    ci = np.asarray((central_data - std, central_data + std))
    kwargs.update({"central_data": central_data, "ci": ci, "data": data})
    seaborn.timeseries._plot_ci_band(*args, **kwargs)

seaborn.timeseries._plot_std_bars = _plot_std_bars
seaborn.timeseries._plot_std_band = _plot_std_band


class CellListPlot(object):
    def __init__(self, cell_list):
        self.cell_list = cell_list

    def hist_property(self, ax=None, tgt='length'):
        if tgt == 'length':
            values = np.array([c.length for c in self.cell_list]) * (cfg.IMG_PIXELSIZE / 1000)
            title = 'Cell length'
            xlabel = r'Length ($\mu m$)'
        elif tgt == 'radius':
            values = np.array([c.radius for c in self.cell_list]) * (cfg.IMG_PIXELSIZE / 1000)
            title = 'Cell radius'
            xlabel = r'Radius ($\mu m$)'
        elif tgt == 'area':
            values = np.array([c.area for c in self.cell_list]) * (cfg.IMG_PIXELSIZE / 1000)**2
            title = 'Cell area'
            xlabel = r'Area ($\mu m^{2}$)'
            #todo check these numbers!!!
        elif tgt == 'volume':
            values = np.array([c.volume for c in self.cell_list]) * (cfg.IMG_PIXELSIZE / 1000) ** 3
            title = 'Cell volume'
            xlabel = r'Volume ($\mu m^{3}$ / fL)'
        else:
            raise ValueError('Invalid target')
        ax_d = sns.distplot(values, kde=False, ax=ax)
        ax_d.set_title(title)
        ax_d.set_xlabel(xlabel)
        ax_d.set_ylabel('Cell count')

        return ax_d

    def plot_dist(self, ax=None, mode='r', src='', std='std_band', norm_y=False, norm_x=False, storm_weights='points', **kwargs):
        """

        :param mode: r, l, or a for radial, longitudinal or angular
        :param src: which data source to use
        :param std: band or bar style std error bars
        :param norm_y: normalize distribution wrt y
        :param norm_x normalize distribution wrt r, l, (not alpha)
        :param kwargs: are passed to plot
        :return:
        """

        if norm_x:
            stop = cfg.R_DIST_NORM_STOP
            step = cfg.R_DIST_NORM_STEP
        else:
            stop = cfg.R_DIST_STOP
            step = cfg.R_DIST_STEP

        if mode == 'r':
            x, out_arr = self.cell_list.r_dist(stop, step, src=src, norm_x=norm_x, storm_weight=storm_weights)
            out_arr = np.nan_to_num(out_arr)
            title = 'Radial Distribution'
        elif mode == 'l':
            raise NotImplementedError()
        elif mode == 'a':
            raise NotImplementedError()

        if norm_y:
            a_max = np.max(out_arr, axis=1)
            out_arr = out_arr / a_max[:, np.newaxis]

        t = x if norm_x else x * (cfg.IMG_PIXELSIZE / 1000)
        t_units = 'norm' if norm_x else '$\mu m$'
        ax_out = sns.tsplot(data=out_arr, time=t, estimator=np.mean, err_style=std, ax=ax, **kwargs)
        ax_out.set_xlabel('Distance ({})'.format(t_units))
        ax_out.set_ylabel('Signal intensity')
        ax_out.set_title(title)

        if norm_y:
            ax_out.ylim(0, 1.1)
        ax_out.tight_layout()


class CellPlot(object):
    def __init__(self, cell_obj):
        self.c = cell_obj

    def plot_midline(self, ax=None, coords='mpl', **kwargs):
        """
        Plot the final found function and xl, xr
        :param coords:
        :param kwargs:
        :return:
        """

        x = np.linspace(self.c.coords.xl, self.c.coords.xr, 100)
        y = self.c.coords.p(x)
        if 'color' not in kwargs:
            kwargs['color'] = 'r'
        if coords == 'mpl':
            x, y = self.c.coords.transform(x, y, src='cart', tgt='mpl')

        ax = plt.gca() if ax is None else ax
        ax.plot(x, y, **kwargs)

        return ax

    def plot_binary_img(self, ax=None, **kwargs):
        if 'interpolation' not in kwargs:
            kwargs['interpolation'] = 'nearest'

        ax = plt.gca() if ax is None else ax
        ax.imshow(self.c.data.binary_img, **kwargs)

        return ax

    def plot_simulated_shape(self, ax=None, **kwargs):
        if 'interpolation' not in kwargs:
            kwargs['interpolation'] = 'nearest'
        img = self.c.coords.rc < self.c.coords.r

        ax = plt.gca() if ax is None else ax
        ax.imshow(img, **kwargs)

        return ax

    def plot_bin_fit_comparison(self, ax=None, **kwargs):
        if 'interpolation' not in kwargs:
            kwargs['interpolation'] = 'nearest'
        img = self.c.coords.rc < self.c.coords.r

        ax = plt.gca() if ax is None else ax
        ax.imshow(3 - (2*img + self.c.data.binary_img), **kwargs)

        return ax

        #todo sequential colormap

    def plot_outline(self, ax=None, coords='mpl', **kwargs):
        #todo: works but: semicircles are not exactly from 0 to 180 but instead depend on local slope (xr, xl)
        #todo: dx sign depends on slope sign (f_d > 0, dx < 0), vice versa?

        x = np.linspace(self.c.coords.xl, self.c.coords.xr, 500)
        p_dx = self.c.coords.p_dx(x)

        dy_t = np.sqrt(self.c.coords.r**2 * (1 + 1 / (1 + (1 / p_dx**2))))
        dx_t = np.sqrt(self.c.coords.r**2 / (1 + (1 / p_dx**2)))
        x_t = x - ((p_dx/np.abs(p_dx)) * dx_t)
        y_t = self.c.coords.p(x) + dy_t

        x_b = (x + ((p_dx/np.abs(p_dx)) * dx_t))[::-1]
        y_b = (self.c.coords.p(x) - dy_t)[::-1]

        #Left semicirlce
        psi = np.arctan(-self.c.coords.p_dx(self.c.coords.xl))

        th_l = np.linspace(-0.5*np.pi+psi, 0.5*np.pi + psi, num=200)
        cl_dx = self.c.coords.r*np.cos(th_l)
        cl_dy = self.c.coords.r*np.sin(th_l)

        cl_x = self.c.coords.xl - cl_dx
        cl_y = self.c.coords.p(self.c.coords.xl) + cl_dy

        #Right semicircle
        psi = np.arctan(-self.c.coords.p_dx(self.c.coords.xr))

        th_r = np.linspace(0.5*np.pi-psi, -0.5*np.pi-psi, num=200)
        cr_dx = self.c.coords.r*np.cos(th_r)
        cr_dy = self.c.coords.r*np.sin(th_r)

        cr_x = cr_dx + self.c.coords.xr
        cr_y = cr_dy + self.c.coords.p(self.c.coords.xr)

        x_all = np.concatenate((cl_x, x_t, cr_x, x_b))
        y_all = np.concatenate((cl_y, y_t, cr_y, y_b))

        x_all, y_all = self.c.coords.transform(x_all, y_all, src='cart', tgt=coords)

        ax = plt.gca() if ax is None else ax
        ax.plot(x_all, y_all, color='r', **kwargs)

        return ax

    def plot_dist(self, ax=None, mode='r', src='', norm_y=False, norm_x=False, storm_weights='points'):

        if mode == 'r':
            if norm_x:
                stop = cfg.R_DIST_NORM_STOP
                step = cfg.R_DIST_NORM_STEP
            else:
                stop = cfg.R_DIST_STOP
                step = cfg.R_DIST_STEP
            x, y = self.c.r_dist(stop, step, src=src, norm_x=norm_x, storm_weight=storm_weights)

            if norm_y:
                y /= y.max()

        elif mode == 'l':
            raise NotImplementedError
        elif mode == 'a':
            raise NotImplementedError
        else:
            raise ValueError('Distribution mode {} not supported'.format(mode))

        x = x if norm_x else x * (cfg.IMG_PIXELSIZE / 1000)
        xunits = 'norm' if norm_x else '$\mu m$'

        yunits = 'norm' if norm_y else 'a.u.'

        ax = plt.gca() if ax is None else ax
        ax.plot(x, y)
        ax.set_xlabel('Distance ({})'.format(xunits))
        ax.set_ylabel('Intensity ({})'.format(yunits))
        if norm_y:
            ax.set_ylim(0, 1.1)

        return ax

    def _plot_intercept_line(self, x_pos, coords='cart', **kwargs):
        x = np.linspace(x_pos - 10, x_pos + 10, num=200)
        f_d = self.c.coords.p_dx(x_pos)
        y = (-x / f_d) + self.c.coords.p(x_pos) + (x_pos / f_d)

        x, y = self.c.coords.transform(x, y, src='cart', tgt=coords)

        plt.plot(x, y)

    def figure(self):
        plt.figure()

    def show(self):
        plt.show()
