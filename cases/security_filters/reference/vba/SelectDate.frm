Attribute VB_Name = "SelectDate"
Attribute VB_Base = "0{E5C04E2F-C1FD-40B3-A7E6-6B466AE4E86E}{0526CA6D-9128-4F7D-BCA1-B81908B7D101}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = False
Public userOption
Private Fecha As String, Linea As String, HoraSalida As String, Destino As String, Asientos As String
Private FirstRow As Integer
Private sourceSheet As Worksheet


Private Sub DateCancel_Click()
    userOption = vbCancel
    processOperations.closeSource
    SelectDate.Hide
End Sub

Private Sub DateOk_Click()
    Dim selectedDate As Date
    Dim cnt, cnt1 As Integer
    Dim filterRange As Range
    Dim f As Filter
    Dim currentFiltRange As String
    Dim oRng As Range
    Dim oColRng As Range
    Dim oInRng As Range
    

    
    userOption = vbOK
    'Verificamos que se ha seleccionado un solo dia
    With sourceSheet
        'Set filterRange = .AutoFilter.Filters(1)
        '
        For Each f In .AutoFilter.Filters
            If f.On Then
                currentFiltRange = .AutoFilter.Range.Address
                'c1 = Right(f.Criteria1, Len(f.Criteria1) - 1)
                Set oColRng = .AutoFilter.Range 'oWS.Range("A2:A5000")
                Set oRng = sourceSheet.Cells.SpecialCells(xlCellTypeVisible)
                Set oInRng = Intersect(.Cells.SpecialCells(xlCellTypeVisible), .Range(currentFiltRange))

                'c1 = .AutoFilter.Range.Cells(FirstRow, Fecha)
                c1 = Str(oInRng.Areas(2).Cells(1, 1))
                For i = 3 To oInRng.Areas.Count
                    c2 = Str(oInRng.Areas(i).Cells(1, 1))
                    If (c2 <> c1) Then
                        MsgBox "Debe seleccionar un único dia"
                        Exit Sub
                    End If
                Next i
                cnt = FirstRow
                cnt1 = 2
                processOperations.paso1.Cells(2, "A") = c1
                While IsDate(.Cells(cnt, Fecha))
                    If Str(.Cells(cnt, Fecha)) = c1 Then '
                        processOperations.paso1.Cells(cnt1, "B") = .Cells(cnt, Linea)
                        processOperations.paso1.Cells(cnt1, "C") = .Cells(cnt, HoraSalida)
                        processOperations.paso1.Cells(cnt1, "D") = .Cells(cnt, Destino)
                        processOperations.paso1.Cells(cnt1, "E") = .Cells(cnt, Asientos)
                        cnt1 = cnt1 + 1
                    End If
                    cnt = cnt + 1
                Wend
            Else
                MsgBox "Debe seleccionar un único dia"
                Exit Sub
            End If
        Next

        
        
    End With
    
    
    processOperations.main Fecha, Linea, HoraSalida, Destino, Asientos, cnt1 - 1
    SelectDate.Hide
End Sub

Public Sub initialize_combo(Label1 As String, Label2 As String, Lin As String, HoraS As String, Dest As String, Asi As String, row As Integer, sheet As Worksheet)
    Hoja.Caption = Label1
    columna.Caption = Label2
    
    Fecha = Label2
    Linea = Lin
    HoraSalida = HoraS
    Destino = Dest
    Asientos = Asi
    FirstRow = row
    Set sourceSheet = sheet


End Sub

