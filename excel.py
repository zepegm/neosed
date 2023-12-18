import win32com.client
import pythoncom
import openpyxl
import warnings


def rgb_to_hex(rgb):
    bgr = (int(rgb[2]), int(rgb[1]), int(rgb[0]))
    strValue = '%02x%02x%02x' % bgr
    # print(strValue)
    iValue = int(strValue, 16)
    return iValue

class open_xls:
    def __init__(self, filepath):
        self.wb = openpyxl.load_workbook(filepath)
        self.sheet_obj = self.wb.active

    def getCell(self, r, c):
        cell_obj = self.sheet_obj.cell(row=r, column=c)
        return cell_obj.value

class xls:
    def __init__(self, planilha):
        self.app = win32com.client.Dispatch("Excel.Application", pythoncom.CoInitialize())
        self.wb = self.app.Workbooks(planilha)

        #try :
            #self.objCOM = self.app.Workbooks(self.app.ActiveWorkbook.Name)
        #except:
            #self.objCOM = None

    def getCountA(self, name, endereco):
        return self.wb.WorksheetFunction.CountA(self.app.Worksheets(name).Range(endereco))

    def getValCell(self, name, endereco):
        return self.wb.Worksheets(name).Range(endereco).value
    
    def getValCellNumbes(self, name, endereco, row, col):
        return self.wb.Worksheets(name).Range(endereco).Cells(row, col).value

    def setValCell(self, name, endereco, val):
        self.wb.Worksheets(name).Range(endereco).value = val

    def setValCellNumbers(self, name, endereco, val, row, col):
        self.wb.Worksheets(name).Range(endereco).Cells(row, col).value = val
    
    def getActiveRow(self):
        return self.wb.ActiveCell.Row
    
    def setRowHeight(self, row, height):
        self.wb.Rows(str(row) + ":" + str(row)).RowHeight = height

    def insertPhoto(self, name, caminho, endereco):
        print(caminho)
        photo = self.wb.Worksheets(name).Pictures().Insert(caminho)
        photo.Top = self.wb.Worksheets(name).Range(endereco).Top
        photo.Left = self.wb.Worksheets(name).Range(endereco).Left + 3
        photo.height = 516.487609863281 
        photo.width = 569.498657226563 

    def setColorBackground(self, name, endereco, rgb):
        self.wb.Worksheets(name).Range(endereco).Interior.Color = rgb_to_hex(rgb)
