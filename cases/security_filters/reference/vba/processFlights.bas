Attribute VB_Name = "processFlights"
Dim paxFranjas(288) As Integer

Sub calcular_vuelos_franja()

    Dim hora As Integer
    Dim j As Integer
    Dim franja As Integer
    Dim indice As String
    
    'Franja  L_Linea Hora    Destino Aeropuerto  NumAsientos NivelOcupacion  CorrecionFranja Distribucion
    j = 2
    While (Worksheets(1).Cells(j, "C") <> "")
        franja = (Hour(Worksheets(1).Cells(j, "C")) * 60 + Minute(Worksheets(1).Cells(j, "C"))) / 5
        Worksheets(2).Cells(j, "B") = franja
        Worksheets(2).Cells(j, "C") = Worksheets(1).Cells(j, "B")
        Worksheets(2).Cells(j, "D") = Worksheets(1).Cells(j, "C")
        Worksheets(2).Cells(j, "E") = Worksheets(1).Cells(j, "D")
        '=INDICE(DESTINOS,COINCIDIR(C12,IATA)+1)
        indice = "=INDEX(DESTINOS,MATCH(E" + Trim(Str(j)) + ",IATA)+1)"
        Worksheets(2).Cells(j, "F").formula = indice
     
        Worksheets(2).Cells(j, "G") = Worksheets(1).Cells(j, "E")
        Worksheets(2).Cells(j, "H") = 1
        Worksheets(2).Cells(j, "I") = 0
        Worksheets(2).Cells(j, "J") = "DistribucionErlang"
        
        j = j + 1
    Wend
    

End Sub

Sub calcula_pax_franja()
    Dim paxVuelo, estimatedPax, j As Integer
    Dim factor As Double
    Dim oleada As Integer
    
    For i = 1 To 288
        paxFranjas(i) = 0
    Next
    
    j = 2
    While Worksheets(2).Cells(j, "B") <> ""
        paxVuelo = aplicarDistribucion(Worksheets(2).Cells(j, "B"), _
                                       Worksheets(2).Cells(j, "G"), _
                                       Worksheets(2).Cells(j, "H"), _
                                       Worksheets(2).Cells(j, "I"), _
                                       Worksheets(2).Cells(j, "J"))
         j = j + 1
        'AplicarDistribucion(current.ListaDeVuelos[6,i_Indice],current.ListaDeVuelos[1,i_Indice]+current.ListaDeVuelos[5,i_Indice]-7,i_Indice,current.ListaDeVuelos[2,i_Indice],current.ListaDeVuelos[4,i_Indice]);
        'i_Indice:=i_Indice+1;
             
    Wend

    For i = 1 To 288
        Worksheets(3).Cells(i + 1, "D") = paxFranjas(i)
    Next
End Sub

Function aplicarDistribucion(franjaVuelo As Integer, _
                             pax As Integer, _
                             factor As Double, _
                             oleada As Integer, _
                             dist As String) As Integer

    Dim pax_franjas(29) As Integer
    Dim j, distI, later, previous, totalPax, p, accPax, res As Integer
    Dim distribucion(29) As Double

    later = franjaVuelo + oleada
    totalPax = Round(pax * factor, 0)
    
    If Not later <= 7 Then
        distI = 0
        For j = 1 To 5
            If dist = Worksheets(4).Cells(1, j) Then
                distI = j
            End If
        Next
        If distI = 0 Then
            distI = 2
        End If
            
        For j = 3 To 31
            distribucion(j - 2) = Worksheets(4).Cells(j, distI)
        Next
        
        For j = 1 To 29
            p = Round(totalPax * distribucion(j), 0)
            pax_franjas(j) = p
            accPax = accPax + p
        Next
        
        
        res = totalPax - accPax
        
        j = 0
        
        While (j < 28) And ((later - j) >= 1)
            paxFranjas(later - j) = paxFranjas(later - j) + pax_franjas(j + 1)
            j = j + 1
        Wend
        
        aplicarDistribucion = 20
    Else
        aplicarDistribucion = 0
    End If
End Function


