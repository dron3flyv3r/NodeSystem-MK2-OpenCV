import dearpygui.dearpygui as dpg
import cv2
import numpy as np

from NodeEditor.Core.Node import Node
from NodeEditor.Core.NodePackage import NodePackage

class RGBHistogram(Node):
    def __init__(self):
        super().__init__("RGB Histogram", "Analysis", 400)
        self.add_input("image")

        # UI controls
        self.plot_tag = dpg.generate_uuid()
        self.series_r_tag = dpg.generate_uuid()
        self.series_g_tag = dpg.generate_uuid()
        self.series_b_tag = dpg.generate_uuid()

        self._default_xdata = [0.0 + i for i in range(256)]
        self._default_ydata = [0.0] * 256

    def calculate_histogram(self, image):
        if image is None:
            return None, None

        b, g, r = cv2.split(image)

        blue_hist = cv2.calcHist([b], [0], None, [256], [0, 256])
        green_hist = cv2.calcHist([g], [0], None, [256], [0, 256])
        red_hist = cv2.calcHist([r], [0], None, [256], [0, 256])

        return self._default_xdata, (red_hist, green_hist, blue_hist)

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        data = inputs[0]
        if data is None or data.image_or_mask is None:
            return []

        image = data.image_or_mask

        if len(image.shape) < 3:
            return []

        x_data, histograms = self.calculate_histogram(image)

        if histograms is None:
            return []

        red_hist, green_hist, blue_hist = histograms

        dpg.set_value(self.series_r_tag, [x_data, [i[0] for i in red_hist]])
        dpg.set_value(self.series_g_tag, [x_data, [i[0] for i in green_hist]])
        dpg.set_value(self.series_b_tag, [x_data, [i[0] for i in blue_hist]])
        
        max_val = max(red_hist.max(), green_hist.max(), blue_hist.max())
        dpg.set_axis_limits(str(self.plot_tag) + "yaxis", 0, min(max_val, 25000))

        return []

    def compose(self):
        small_window_w = 500
        small_window_h = 300

        with dpg.plot(
            width=small_window_w,
            height=small_window_h,
            tag=self.plot_tag,
            no_menus=True,
        ):
            # Legend
            dpg.add_plot_legend(horizontal=True, location=dpg.mvPlot_Location_NorthEast)
            # x axis
            dpg.add_plot_axis(dpg.mvXAxis, tag=str(self.plot_tag) + "xaxis")
            dpg.set_axis_limits(dpg.last_item(), 0, 256)

            # y axis
            dpg.add_plot_axis(dpg.mvYAxis, tag=str(self.plot_tag) + "yaxis")
            dpg.add_line_series(
                self._default_xdata,
                self._default_ydata,
                label="B",
                parent=str(self.plot_tag) + "yaxis",
                tag=self.series_b_tag,
            )
            dpg.add_line_series(
                self._default_xdata,
                self._default_ydata,
                label="R",
                parent=str(self.plot_tag) + "yaxis",
                tag=self.series_r_tag,
            )
            dpg.add_line_series(
                self._default_xdata,
                self._default_ydata,
                label="G",
                parent=str(self.plot_tag) + "yaxis",
                tag=self.series_g_tag,
            )
