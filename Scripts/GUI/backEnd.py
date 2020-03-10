import pandas as pd
import re
import time
from random import random

from Scripts.Exceptions import *;

class Purchase_Sales_Match(object):
    compiledExp = re.compile('/[A-Z]*[0-9]+[A-Z]*/')
    check = ["1920", '2020', '2019']

    def __int__(self):
        # Details of file 1
        self.file1Path = None
        self.file1Header = None
        self.file1Sheet = None

        # details of file 2
        self.file2Path = None
        self.file2Header = None
        self.file2Sheet = None

        self.outFilePath = None

        self.myExcel: pd.ExcelFile = None
        self.givenExcel: pd.ExcelFile = None

        self.myVouchar: pd.DataFrame = None
        self.givenVouchar: pd.DataFrame = None
        self.mergedData: pd.DataFrame = None
        self.MatchedDetails : pd.DataFrame = None
        self.notMatched_myside: pd.DataFrame = None
        self.notMatched_otherside: pd.DataFrame = None

        # columns values
        self.mycols =  ['Particulars', 'GSTIN/UIN', 'Invoice No.', 'Taxable Value', 'Integrated Tax Amount',
                          'Central Tax Amount', 'State Tax Amount', 'Total Tax Amount']
        self.gvcols =['GSTIN of supplier', 'Trade/Legal name of the Supplier','Invoice details Invoice number', 'Invoice details Invoice Value (₹)',
                          'Taxable Value (₹)', 'Tax Amount Integrated Tax  (₹)', 'Tax Amount Central Tax (₹)',
                          'Tax Amount State/UT tax (₹)']
        # success signals
        self.Done_with_match: bool = False


    #     panda part
    @staticmethod
    def validation(n):
        return n and not (n == '')

    @staticmethod
    def join(i):
        si = list(i)
        if len(si) >= 2:
            for j in range(len(si)):
                if ('Unnamed' in si[j]):
                    del si[j]

        return " ".join(si)

    @staticmethod
    def makeInt(n):

        def sanit(x):
            inter = re.search("\d+", x[1:-1]).group()
            for i in Purchase_Sales_Match.check:
                if (i in inter):
                    return 0
            return int(inter)

        return list(map(sanit, n))

    @staticmethod
    def spl(i):
        i = str(i)
        if ("/" not in i):
            return i
        try:
            j = i.replace('/', "//")
            j = "/{}/".format(j)
            print(j)
            val = Purchase_Sales_Match.compiledExp.findall(j)
            if (len(val) == 0):
                raise ValueError
            ret = max(Purchase_Sales_Match.makeInt(val))
            return str(ret)
        except:
            if i!='nan':
                try:
                    val = re.findall('\d+', i)
                    return str(max(list(map(int, val))))
                except:
                    return i
            return  i

    @staticmethod
    def float_compare(a, b):
        a, b = round(float(a)), round(float(b))
        if a == b:
            return True
        else:
            if abs(a - b) <= 1:
                return True
            else:
                return False

    def format_header(self):
        try:
            mv, gv = self.myVouchar.keys(), self.givenVouchar.keys()
            m = [self.join(i)
                 for i in mv]
            g = [self.join(i)
                 for i in gv]
            return (m, g)
        except:
            raise MsgException("Wrong Header format")

    def data_sanit(self):
        mvNew, gvNew = self.myVouchar.keys(), self.givenVouchar.keys()
        for i in mvNew:
            if i not in self.mycols:
                del self.myVouchar[i]

        for i in gvNew:
            if i not in self.gvcols:
                del self.givenVouchar[i]
        return


    def format_invoice(self):
        matching_excel = {}

        # self.myVouchar["Invoice"] = [self.spl(i) for i in self.myVouchar["Invoice No."]]
        # self.givenVouchar["Invoice"] = [self.spl(i) for i in self.givenVouchar["Invoice details Invoice number"]]

        self.myVouchar["Invoice"] = self.myVouchar["Invoice No."].copy()
        self.givenVouchar["Invoice"] = self.givenVouchar["Invoice details Invoice number"].copy()

        matching_excel['Invoice']  = self.myVouchar["Invoice No."].append(self.givenVouchar["Invoice details Invoice number"])
        matching_excel['Sanitized Data'] = self.myVouchar["Invoice"].append(self.givenVouchar["Invoice"])

        self.match_report = pd.DataFrame(matching_excel)
        return

    def match_work(self):
        count = 0
        self.Done_with_match = False

        matchresult = []
        data = self.mergedData
        notMatched_myside = {}
        notMatched_otherside = {}
        MatchedDetails = []

        mycols = self.mycols.copy()
        gvcols = self.gvcols.copy()
        print("editing GST no")
        mycols[1] = gvcols[0] = "GSTno."
        print("editing done")

        for i in mycols:
            notMatched_myside[i]=[]

        for i in gvcols:
            notMatched_otherside[i]=[]

        for i, j in data.iterrows():
            r: bool = True
            gst1, gst2 = j['Taxable Value'], j['Taxable Value (₹)']
            igst1, igst2 = j['Integrated Tax Amount'], j['Tax Amount Integrated Tax  (₹)']
            cgst1, cgst2 = j['Central Tax Amount'], j['Tax Amount Central Tax (₹)']
            sgst1, sgst2 = j['State Tax Amount'], j['Tax Amount State/UT tax (₹)']

            if not Purchase_Sales_Match.float_compare(gst1, gst2):
                r = False
            if not Purchase_Sales_Match.float_compare(igst1, igst2):
                r = False
            if not Purchase_Sales_Match.float_compare(sgst1, sgst2):
                r = False
            if not Purchase_Sales_Match.float_compare(cgst1, cgst2):
                r = False
            if r:
                count += 1
                matchresult.append("MATCHED")
                MatchedDetails.append(j)
            else:
                matchresult.append("NOT MATCHED")
                if int(gst1)==0 and int(igst1)==0 and int(cgst1)==0 and int(sgst1)==0:
                    for k in gvcols:
                        notMatched_otherside[k].append(j[k])
                elif int(gst2)==0 and int(igst2)==0 and int(cgst2)==0 and int(sgst2)==0:
                    for k in mycols:
                        notMatched_myside[k].append(j[k])
                else:
                    for k in gvcols:
                        notMatched_otherside[k].append(j[k])

                    for k in mycols:
                        notMatched_myside[k].append(j[k])


        data['Result'] = matchresult
        print("Found match in {0}/{1}".format(count, len(matchresult)))
        rate = count*100/len(matchresult)
        print("Matched: {}%".format(round(rate,2)))
        self.MatchedDetails = pd.DataFrame(MatchedDetails)
        self.notMatched_myside = pd.DataFrame(notMatched_myside)
        self.notMatched_otherside = pd.DataFrame(notMatched_otherside)
        self.Done_with_match = True
        return

    # def attach(self,left, right):
    #     l = left.append(right)
    #     # print(l)
    #     return l

    # def combo(self, left: pd.DataFrame, right: pd.DataFrame, on=None):
    #
    #     left['visited'] = [0 for _ in range(len(left))]
    #     right['visited'] = [0 for _ in range(len(right))]
    #
    #     merge_result = []
    #
    #     for i, row1 in left.iterrows():
    #         for j, row2 in right.iterrows():
    #             if (row1['visited'] == 0 and row2['visited'] == 0):
    #                 if (row1[on[0]] == row2[on[0]] and row1[on[1]] == row2[on[1]]):
    #                     row1['visited'] = row2['visited'] = 1
    #                     # obj = {'A': row1['A'], 'B': row2['B'], 'value1': row1["value"], 'value2': row2['value']}
    #                     # obj = row1.append(row2)
    #                     obj = self.attach(row1, row2)
    #                     merge_result.append(obj)
    #                     print(i,j)
    #                     break
    #
    #     return pd.DataFrame(merge_result)

    def convert_to_float(self):
        # self.givenVouchar['Taxable Value (₹)'] = self.givenVouchar['Taxable Value (₹)'].astype(float)
        # self.givenVouchar['Tax Amount Integrated Tax  (₹)'] = self.givenVouchar[
        #     'Tax Amount Integrated Tax  (₹)'].astype(float)
        # self.givenVouchar['Tax Amount Central Tax (₹)'] = self.givenVouchar['Tax Amount Central Tax (₹)'].astype(float)
        # self.givenVouchar['Tax Amount State/UT tax (₹)'] = self.givenVouchar['Tax Amount State/UT tax (₹)'].astype(float)

        self.myVouchar[
            [
                'Taxable Value',
                'Integrated Tax Amount',
                'Central Tax Amount',
                'State Tax Amount'
            ]
        ] = self.myVouchar[
            [
                'Taxable Value',
                'Integrated Tax Amount',
                'Central Tax Amount',
                'State Tax Amount'
            ]
        ].astype(float)

        self.givenVouchar[
            [
                'Taxable Value (₹)',
                'Tax Amount Integrated Tax  (₹)',
                'Tax Amount Central Tax (₹)',
                'Tax Amount State/UT tax (₹)'
            ]
        ] = self.givenVouchar[
            [
                'Taxable Value (₹)',
                'Tax Amount Integrated Tax  (₹)',
                'Tax Amount Central Tax (₹)',
                'Tax Amount State/UT tax (₹)'
            ]
        ].astype(float)

    def check_positive(self,data,cols=[]):
        for i in cols:
            if data[i]<0:
                return False
        return True

    def format_type(self):
        self.convert_to_float()
        mv = []
        gv = []
        mvCols = [
            'Taxable Value',
            'Integrated Tax Amount',
            'Central Tax Amount',
            'State Tax Amount'
        ]
        gvCols = [
            'Taxable Value (₹)',
            'Tax Amount Integrated Tax  (₹)',
            'Tax Amount Central Tax (₹)',
            'Tax Amount State/UT tax (₹)'
        ]
        for i, row in self.myVouchar.iterrows():
            if self.check_positive(row, mvCols):
                mv.append('d')
            else:
                mv.append('c')

        for i, row in self.givenVouchar.iterrows():
            if self.check_positive(row, gvCols):
                gv.append('d')
            else:
                gv.append('c')
        self.myVouchar['type'] = mv
        self.givenVouchar['type'] = gv

    def main(self):
        start = time.time()
        self.Done_with_match = False
        try:
            if self.myExcel:
                self.myVouchar = pd.read_excel(self.myExcel, self.file1Sheet, header=self.file1Header).fillna(0)
            else:
                # raise exception
                raise ExcelReadException(self.file1Path)


            if self.givenExcel:
                self.givenVouchar = pd.read_excel(self.givenExcel, self.file2Sheet, header=self.file2Header).fillna(0)
            else:
                #raise exception
                raise ExcelReadException(self.file2Path)

            if self.myExcel and self.givenExcel:
                self.myVouchar.columns, self.givenVouchar.columns = self.format_header()

                # Sanitary check of data
                self.data_sanit()

                #  format invoice
                self.format_invoice()

                #  check columns
                self.myVouchar.rename(columns={'GSTIN/UIN': 'GSTno.'}, inplace=True)
                self.givenVouchar.rename(columns={'GSTIN of supplier': 'GSTno.'}, inplace=True)

                #sorting Data
                self.myVouchar.sort_values(['GSTno.', 'Invoice'], ascending=[True, True])

                # format type => debit or credit
                self.format_type()

                # Combine separate bills in GST side
                newVouchar = self.givenVouchar.groupby(['GSTno.', 'Invoice','type'])[
                    [
                        'Taxable Value (₹)',
                        'Tax Amount Integrated Tax  (₹)',
                        'Tax Amount Central Tax (₹)',
                        'Tax Amount State/UT tax (₹)'
                    ]
                ].transform('sum')

                for i in newVouchar.keys():
                    self.givenVouchar[i] = newVouchar[i]

                self.givenVouchar = self.givenVouchar.drop_duplicates(subset=['GSTno.', 'Invoice', 'type'])

                #  data join
                self.mergedData = pd.merge(self.myVouchar, self.givenVouchar, on=['GSTno.', 'Invoice', 'type'], how='outer').fillna(0)

                # match
                self.match_work()

                # spliting
                # self.notMatched_myside = self.myVouchar[self.myVouchar['visited'] == 1]
                # self.notMatched_otherside = self.givenVouchar[self.givenVouchar['visited'] == 1]

                # # Creating excel writer
                # outFileWriter = pd.ExcelWriter(self.outFilePath, engine='xlsxwriter')

                # # write into a file
                # # self.normal_status("Creating output file")
                # self.mergedData.to_excel(outFileWriter, sheet_name='All Data')
                # self.MatchedDetails.to_excel(outFileWriter, sheet_name="Matched Data")
                # self.notMatched_myside.to_excel(outFileWriter, sheet_name="My Side")
                # self.notMatched_otherside.to_excel(outFileWriter, sheet_name="GST portal")
                # outFileWriter.save()

                self.write_Result_to_excel()

        except Exception as e:
            print(str(e))
        print("Process finished in : {0} secs".format(round(time.time() - start), 3))


    def write_Result_to_excel(self):
        # Creating excel writer
        if self.Done_with_match:
            print("Writting results")
            print(self.outFilePath)
            outFileWriter = pd.ExcelWriter(self.outFilePath, engine='xlsxwriter')

            # write into a file
            self.mergedData.to_excel(outFileWriter, sheet_name='All Data')
            self.MatchedDetails.to_excel(outFileWriter, sheet_name="Matched Data")
            self.notMatched_myside.to_excel(outFileWriter, sheet_name="My Side")
            self.notMatched_otherside.to_excel(outFileWriter, sheet_name="GST portal")
            self.match_report.to_excel(outFileWriter, sheet_name="Sanit of Invoice Report")
            self.givenVouchar.to_excel(outFileWriter, sheet_name="new sales")
            outFileWriter.save()
            print("DONE")

        else:
            print("Writter is not ready")



