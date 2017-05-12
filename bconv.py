#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import *
from pdfminer.converter import PDFConverter
import csv

class BlackConverter(PDFConverter):

    def __init__(self, rsrcmgr, outfp, pageno=1):
        laparams = LAParams()
        laparams.char_margin=0.1
        PDFConverter.__init__(self, rsrcmgr, outfp, codec='utf-8', laparams=laparams)
        self.lines = []
        self.boxes = []
        self.writer = csv.writer(outfp,
                                 lineterminator='\n')
        self.writer.writerow(["企業・事業場名称",
                              "所在地",
                              "公表日",
                              "違反法条",
                              "事案概要",
                              "その他参考事項"])
        return

    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTContainer):
                for child in item:
                    render(child)
            if isinstance(item, LTTextBox):
                (x0, y0, x1, y1) = item.bbox
                x = int(x0)
                y = int(y0)
                text = item.get_text()
                self.boxes.append(item)
            elif isinstance(item, LTRect):
                (x0, y0, x1, y1) = item.bbox
                w = x1 - x0
                h = y1 - y0
                x = int(x0)
                y = int(y0)
                if h < 2:
                    self.lines.append(y)
            elif isinstance(item, LTPage):
                l1 = self.lines[1:]
                l2 = self.lines[2:]
                lines = zip(l1, l2)
                for (y0, y1) in lines:
                    row = []
                    for b in self.boxes:
                        if y0 > b.bbox[1] > y1:
                            row.append(b)
                    l = len(row)
                    if l == 0:
                        pass
                    elif l == 6:
                        # correct
                        text = map(lambda col: col.get_text().rstrip(), row)
                        name = text[0].replace("\n", "")
                        if len(name) > 30:
                            name = name[:30] + u'…'
                        addr = text[1]
                        date = text[2]
                        violation = text[3]
                        desc = text[4].replace("\n", "")
                        etc = text[5]
                        self.writer.writerow(map(lambda s: s.encode('UTF-8'),
                                                 [name, addr, date, violation, desc, etc]))
                    else:
                        raise Exception("invalid len")
                self.lines = []
                self.boxes = []

        render(ltpage)
        return

def main(argv):
    outfile = "out.csv"
    outfp = open(outfile, "w")
    rsrcmgr = PDFResourceManager(caching=True)
    device = BlackConverter(rsrcmgr, outfp)
    fp = file(argv[1], 'rb')
    pagenos = set()
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for i, page in enumerate(PDFPage.get_pages(fp, pagenos,
                                               caching=True,
                                               check_extractable=True)):
        interpreter.process_page(page)
    fp.close()
    outfp.close()
    device.close()
    return

if __name__ == '__main__':
    main(sys.argv)
