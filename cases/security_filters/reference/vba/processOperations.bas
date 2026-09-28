Attribute VB_Name = "processOperations"
Public num_columnas As Integer
Public num_franjas As Integer
Public DataSource As String
Public paso1 As Worksheet
Dim fvuelos As String
Sub ProcessDataSource()
    Dim Mensaje, Estilo, Título, Ayuda, Ctxt, respuesta
    Mensaje = "Se borraran los datos actuales ¿Desea continuar?"    ' Define el mensaje.
    Estilo = vbYesNo + vbCritical + vbDefaultButton2    ' Define los botones.
    Título = "Importar datos de vuelos "    ' Define el título.
    Ayuda = "DEMO.HLP"    ' Define el archivo de ayuda.
    Ctxt = 1000    ' Define el tema
                   ' el contexto
                   ' Muestra el mensaje.
    respuesta = MsgBox(Mensaje, Estilo, Título, Ayuda, Ctxt)
    If respuesta = vbYes Then    ' El usuario eligió el botón Sí.
        deleteCurrentData
        open_cuadrante
        If processOperations.fvuelos <> "" Then
            With Workbooks
                DataSource = .Application.ActiveWorkbook.Name
            End With
            SelectDataSource.Show
        End If
    End If
End Sub
' procedimiento principal
Sub main(Fecha As String, Linea As String, HoraSalida As String, Destino As String, Asientos As String, total As Integer)
    Dim todo, rango As String
    Dim c As CellFormat
    
    'primero cerramos el origen de datos
    closeSource
    rango = "C2:C" + Trim(Str(total))
    todo = "B2:E" + Trim(Str(total))
    ' ordenamos vuelos seleccionados
    With paso1
        .Range(todo).Sort Key1:=.Range(rango)
        
    End With
    
    

End Sub

Sub open_cuadrante()

    'prompt user to open file
    MyFile = Application.GetOpenFilename("Programación de Vuelos,*.xls") _

    If MyFile <> False Then
        Workbooks.Open _
        Filename:=MyFile, _
        ReadOnly:=True
        processOperations.fvuelos = MyFile
    Else
        processOperations.fvuelos = ""
    End If
 
End Sub
Sub deleteCurrentData()
    'Dim sourceSheet As Worksheet
    Dim cnt As Integer
    Dim rango As String
    
    'sourceSheet = ThisWorkbook.Worksheets("Paso1").Activate
    
    With ThisWorkbook
        cnt = 2
        .Worksheets("Paso1").Activate
        Set paso1 = .Worksheets("Paso1")
        While Cells(cnt, "B") <> ""
            cnt = cnt + 1
        Wend
        If cnt > 2 Then
            rango = "B2:E" + Trim(Str(cnt - 1))
            .Worksheets("Paso1").Range(rango).ClearContents
            'Selection.Clear
            rango = "B2:I" + Trim(Str(cnt - 1))
            .Worksheets("Paso2").Range(rango).ClearContents
        End If
        For i = 1 To 288
            .Worksheets(3).Cells(i + 1, "D") = 0
        Next
    End With
    
    
End Sub
Sub GenerateTables()
    DataSource = SelectDataSource.WipFile.Text
    
    ' ='[DatosWIP 19D.xls]OutPutSimulacionWIP'!$B$2
    ' Workbooks.Open FileName:="Array.xls", ReadOnly:=True
    'Dim sourceBook As Workbooks
    Dim sourceSheet As Worksheet
    Dim B As String
    B = "B" ' PersonasVerificacionTargetasNorte
    'sourceBook = Workbooks(DataSource)
    'sourceSheet = sourceBook.Worksheets("OutputSimulacionWIP").Activate
    'Worksheets("VerificacionTarjetas").Cells(1, 1) = Workbooks(DataSource).Worksheets("OutputSimulacionWIP").Cells(1, B)
    
    'Dim acc(129) As Integer
    

    num_columnas = SelectDataSource.TextBox1
    num_franjas = SelectDataSource.TextBox2
'    num_columnas = 129
'    num_franjas = 6
    
    'Range("A1:A2").Select
    'Selection.ClearContents
    
    Dim acc(200) As Long
    
    ' titulos
    'For i = 1 To 129 ' incluye etiqueta periodo
    For i = 1 To num_columnas ' incluye etiqueta periodo
        Worksheets("Tabla-5min").Cells(1, i + 1) = Workbooks(DataSource).Worksheets("OutputSimulacionWIP").Cells(1, i)
    Next
    
    'For franja = 1 To 288
    For franja = 1 To num_franjas
    
        'For j = 1 To 129
        For j = 1 To num_columnas
            acc(j) = 0
        Next
                
        For j = 1 To 60
            'For i = 1 To 129
            For i = 1 To num_columnas
                acc(i) = acc(i) + Workbooks(DataSource).Worksheets("OutputSimulacionWIP").Cells((franja - 1) * 60 + j + 1, i + 1)
            Next
        Next
        
        Worksheets("Tabla-5min").Cells(franja + 1, 2) = franja
        
        'For i = 1 To 129
        For i = 1 To num_columnas
            Worksheets("Tabla-5min").Cells(franja + 1, i + 2) = Round(acc(i) / 60)
        Next
    
    Next
 
    
End Sub
Sub closeSource()
'cierra el cuadrante de operaciones
    For Each w In Workbooks
        If w.FullName = processOperations.fvuelos Then
            'source = w.ThisWorkbook
            w.Close SaveChanges:=False ', RouteWorkbook:=""
        End If
    Next
End Sub


Sub Boton()
    UserForm1.Show
    
   num_columnas = Cells(1, 1)
   num_franjas = Cells(2, 1)
    UserForm1.Hide
End Sub


