import math

class GerberWriter:
    INTEGER_DIGITS = 6

    def __init__(self, filename, unit='mm', precision=3):
        self.file = open(filename, 'w')
        self.unit = unit
        self.precision = precision
        pass

    def write_comment(self, comment):
        self._write('G04 %s*' % comment)

    def write_header(self):
        number_format = '%d%d' % (self.INTEGER_DIGITS, self.precision)
        self._write_ext_cmd('FSLAX%sY%s' % (number_format, number_format))

        if self.unit == 'mm':
            self._write_ext_cmd('MOMM')
        elif self.unit == 'inch':
            self._write_ext_cmd('MOIN')
        else:
            raise 'invalid unit %s (use "mm" or "inch" instead)' % (self.unit)

    def add_circle_aperture(self, index, diameter=1):
        if index < 10:
            raise 'invalid aperture index (use index >= 10)'
        self._write_ext_cmd('ADD%dC,%s' % (index, self._float_number(diameter)))

    def select_aperture(self, index):
        if index < 10:
            raise 'invalid aperture index (use index >= 10)'
        self._write_cmd('D%d' % (index))

    def move_to(self, x, y):
        self._write_cmd('X%sY%sD02' % (self._number(x), self._number(y)))

    def interpolate_to(self, x, y):
        self._write_cmd('X%sY%sD01' % (self._number(x), self._number(y)))

    def flash_at(self, x, y):
        self._write_cmd('X%sY%sD03' % (self._number(x), self._number(y)))

    def begin_region(self):
        self._write_cmd('G36')
    
    def end_region(self):
        self._write_cmd('G37')

    def begin_interpolate(self):
        self._write_cmd('G01')

    def set_polarity(self, polarity):
        p = 'D' if polarity else 'C'
        self._write_ext_cmd('LP%s' % (p))

    def write(self):
        self._write_header()

    def _write_cmd(self, cmd):
        self._write('%s*' % (cmd))

    def _write_ext_cmd(self, cmd):
        self._write('%%%s*%%' % (cmd))

    def _write(self, str):
        self.file.write(str + '\n')
    

    def _write_header(self):
        self._write('G04 Just a test*')
        self._write('%FSLAXX46Y46*%')
        self._write('%MOMM*%')

    def _number(self, number):
        return str(int(math.floor(number * 10**self.precision)))

    def _float_number(self, number):
        format_str = '%%.%df' % (self.precision)
        return format_str % (number)
