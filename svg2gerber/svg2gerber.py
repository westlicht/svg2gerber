import os
import math
import argparse
import svg2gerber.svg as svg
from svg2gerber.earcut import earcut
from svg2gerber.gerber import GerberWriter

# writer = GerberWriter("test.gko")
# writer.write_comment("just a test gerber file")
# writer.write_header()
# writer.add_circle_aperture(11, 0.25)
# writer.select_aperture(11)
# writer.move_to(0, 0)
# writer.interpolate_to(100, 0)
# writer.interpolate_to(100, 100)
# writer.interpolate_to(0, 100)
# writer.interpolate_to(0, 0)

# writer.move_to(20, 20)
# writer.interpolate_to(80, 20)
# writer.interpolate_to(80, 80)
# writer.interpolate_to(20, 80)
# writer.interpolate_to(20, 20)

conversion_table = [
    {
        "layer": ["Edge.Cuts", "Edgecuts", "Outline"],
        "suffix": "Edge_Cuts.gm1",
        "mode": "contours",
    },
    {
        "layer": ["F.Cu", "Front Copper", "Top Copper", "Copper"],
        "suffix": "F_Cu.gtl",
        "mode": "polygons",
    },
    {
        "layer": ["B.Cu", "Back Copper", "Bottom Copper"],
        "suffix": "B_Cu.gbl",
        "mode": "polygons",
    },
    {
        "layer": ["F.SilkS", "Front Silkscreen", "Top Silkscreen", "Silkscreen"],
        "suffix": "F_SilkS.gto",
        "mode": "polygons",
    },
    {
        "layer": ["B.SilkS", "Back Silkscreen", "Bottom Silkscreen"],
        "suffix": "B_SilkS.gbo",
        "mode": "polygons",
    },
    {
        "layer": ["F.Mask", "Front Soldermask", "Top Soldermask", "Soldermask"],
        "suffix": "F_Mask.gts",
        "mode": "polygons",
    },
    {
        "layer": ["B.Mask", "Back Soldermask", "Bottom Soldermask"],
        "suffix": "B_Mask.gbs",
        "mode": "polygons",
    },
]

# writer.write()


class Converter:
    def __init__(self, filename, precision=0.1):
        self.svg = svg.Svg(filename)
        self.gerber = None
        self.svg_precision = precision

        print("Converting '%s' ..." % (filename))

        for item in conversion_table:
            group = self.find_group_by_id(item["layer"])
            if group:
                layer_filename = os.path.splitext(filename)[0] + "-" + item["suffix"]
                print(
                    "Converting SVG group '%s' to '%s' layer in '%s' ..."
                    % (group.id, item["layer"][0], layer_filename)
                )

                convert = {
                    "contours": self.convert_contours,
                    "polygons": self.convert_polygons,
                }

                convert[item["mode"]](group, layer_filename)

        # self.convert_edgecuts("Edgecuts", "frontpanel-Edge_Cuts.gm1")
        # self.convert_silkscreen("Silkscreen", "frontpanel-F_SilkS.gto")

    def convert_contours(self, group, filename):
        self.start_gerber(filename)
        self.gerber.add_circle_aperture(10, 0.01)
        self.gerber.select_aperture(10)

        items = group.flatten()
        for item in self.remove_duplicate_elements(items):
            segments = item.segments(precision=self.svg_precision)
            for segment in segments:
                self.write_contour(segment)

    def write_contour(self, points):
        points = self.remove_duplicate_points(points)
        if len(points) < 2:
            return
        self.gerber.move_to(points[0].x, -points[0].y)
        for p in points[1:]:
            self.gerber.interpolate_to(p.x, -p.y)
        # if (points[-1] != points[0]):
        #     self.gerber.interpolate_to(points[0].x, -points[0].y)

    def convert_polygons(self, group, filename):
        self.start_gerber(filename)

        items = group.flatten()
        for item in self.remove_duplicate_elements(items):
            segments = item.segments(precision=self.svg_precision)
            self.write_polygon(segments)

    def write_polygon(self, segments):
        # print("write polygon")

        # print(segments)
        points = [[(float(p.x), float(p.y)) for p in segment] for segment in segments]
        data = earcut.flatten(points)
        # print(data)
        indices = earcut.earcut(data["vertices"], data["holes"], data["dimensions"])
        vertices = data["vertices"]
        # print(indices)

        if len(indices) < 3:
            return

        self.gerber.begin_region()

        for i in range(len(indices) // 3):
            i0 = indices[i * 3 + 0]
            i1 = indices[i * 3 + 1]
            i2 = indices[i * 3 + 2]
            p0 = (vertices[i0 * 2], vertices[i0 * 2 + 1])
            p1 = (vertices[i1 * 2], vertices[i1 * 2 + 1])
            p2 = (vertices[i2 * 2], vertices[i2 * 2 + 1])
            self.gerber.move_to(p0[0], -p0[1])
            # self.gerber.begin_interpolate()
            self.gerber.interpolate_to(p1[0], -p1[1])
            self.gerber.interpolate_to(p2[0], -p2[1])
            self.gerber.interpolate_to(p0[0], -p0[1])
            # print(p0, p1, p2)

        self.gerber.end_region()

    def start_gerber(self, filename):
        self.gerber = GerberWriter(filename)
        self.gerber.write_header()

    def find_group_by_id(self, ids):
        if isinstance(ids, str):
            ids = [ids]

        def find(items, id):
            for item in items:
                if isinstance(item, svg.Group):
                    if item.id in ids:
                        return item
                    result = find(item.items, ids)
                    if result:
                        return result
            return None

        return find(self.svg.items, id)

    def elements_equal(self, e1, e2):
        if e1.tag != e2.tag:
            return False
        if e1.text != e2.text:
            return False
        if e1.attrib != e2.attrib:
            return False
        if len(e1) != len(e2):
            return False
        return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

    def remove_duplicate_elements(self, items):
        result = []
        for item in items:
            if any(self.elements_equal(item.elt, i.elt) for i in result):
                # print("skipping duplicate element")
                continue
            result.append(item)
        return result

    def remove_duplicate_points(self, points):
        result = []
        last = None
        for p in points:
            if p == last:
                # print("skipping duplicate point")
                continue
            result.append(p)
            last = p
        return result

    def is_clockwise(self, points):
        sum = 0
        for i in range(len(points)):
            a = points[i]
            b = points[(i + 1) % len(points)]
            sum += (b.x - a.x) * (b.y + a.y)
        # for a, b in zip(points, points[1:]):
        #     sum += (b.x - a.x) * (b.y + a.y)
        return sum > 0


# converter = Converter("test.svg")


def convert(filename, precision):
    print("converting %s with precision %f" % (filename, precision))

    converter = Converter(filename, precision)
    pass


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument("echo")
    parser.add_argument("file", type=argparse.FileType("r"), nargs="+")
    parser.add_argument(
        "-p", "--precision", type=float, default=0.1, help="tesselation precision"
    )

    args = parser.parse_args()

    for f in args.file:
        convert(filename=f.name, precision=args.precision)
