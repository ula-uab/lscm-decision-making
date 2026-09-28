Attribute VB_Name = "UserForm1"
Attribute VB_Base = "0{DE09759C-6CEE-4979-8A73-CD399681335B}{11D5BB4D-244F-4B30-849C-D9F42DDD7472}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = False
Private Sub CommandButton1_Click()
    TextBox1_Change
    TextBox2_Change
    UserForm1.Hide
End Sub

Private Sub TextBox1_Change()
     Sheets("Tabla-5min").Select
     Cells(1, 1) = TextBox1
End Sub

Private Sub TextBox2_Change()
     Sheets("Tabla-5min").Select
     Cells(2, 1) = TextBox2
End Sub
