Attribute VB_Name = "SelectDataSource2"
Attribute VB_Base = "0{FE3C3160-5BAB-4763-B5BE-523EDCE25A68}{E66184D5-A42E-4D0A-8A65-637D87A2FB75}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = False

Private Sub Go_Click()
    OciosidadTotalAgentes
    SelectDataSource2.Hide
End Sub


Private Sub Label1_Click()

End Sub

Private Sub Label2_Click()

End Sub

Private Sub UserForm_Click()

End Sub

Private Sub WipFile_Change()

End Sub

Private Sub WipFile_Enter()
    WipFile.Text = "ConfiguracionFiltros-19.xls"
End Sub
