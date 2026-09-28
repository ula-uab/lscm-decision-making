Attribute VB_Name = "SelectDataSource"
Attribute VB_Base = "0{A0C39FF9-1297-44A6-9682-D988ACDC10A4}{16E40F3F-AD75-4C89-8146-435DC6587F23}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = False
Private Sub Cancel_Click()
    processOperations.closeSource
    ' cierra la ventana
    SelectDataSource.Hide
End Sub




Private Sub Go_Click()
    Dim data As Variant
    Dim Hoja As String
    Dim cnt, inicial As Integer
    Dim dateRange As Range
    Dim filterArray()
    Dim currentFiltRange As String
    Dim currentSheet As Worksheet
    Dim filtros As Filter

    
    Workbooks(processOperations.DataSource).Activate
    With ActiveWorkbook
        Hoja = .ActiveSheet.Name
        cnt = Val(FirstRow.Text)
        inicial = cnt
        If Not IsDate(.ActiveSheet.Cells(cnt, Fecha.Text)) Then
            MsgBox "La celda de inicio indicada no es una fecha"
            Exit Sub
        End If
        While IsDate(.ActiveSheet.Cells(cnt, Fecha.Text))
            cnt = cnt + 1
        Wend
        If cnt > inicial Then
            rango = Fecha.Text + Trim(inicial - 1) + ":" + Fecha.Text + Trim(Str(cnt - 1))
            Set dateRange = .ActiveSheet.Range(rango)
        End If
        
        dateRange.AutoFilter field:=1
        ' dateRange.Select
       
        Set currentSheet = .ActiveSheet

        SelectDate.initialize_combo Hoja, Fecha.Text, Linea.Text, HoraSalida.Text, Destino.Text, Asientos.Text, Val(FirstRow.Text), currentSheet
    
        SelectDate.Show

        
    End With
    
    ' cierra la ventana
    SelectDataSource.Hide
End Sub


Private Sub WipFile_Enter()
    WipFile.Text = "T"
End Sub

Private Sub Help_Click()
    MsgBox "Compruebe que, en la hoja activa, las columna indicadas contienen la informacion solicitada."
End Sub

Private Sub SelectDate_Initialize()

End Sub




