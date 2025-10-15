Attribute VB_Name = "modExtractFormulas"
Option Explicit
'==========================
' Module: modExtractFormulas (Step 1)
'==========================

Private Const HDR_RATE As String = "RATE"
Private Const HDR_FORM As String = "Formula"
Private Const EXCLUDE_SHEET1 As String = "FEB"
Private Const EXCLUDE_SHEET2 As String = "InvoiceData"
Private Const EXCLUDE_SHEET3 As String = "SUMMARY"

Public Sub ExtractFormulasWithExclusion()
    Dim t0 As Single: t0 = Timer
    On Error GoTo ErrH
    AppBegin "ExtractFormulas"
    LogActionSafe "ExtractFormulas", "BEGIN"

    ExtractFormulas_Impl

    LogActionSafe "ExtractFormulas", "END " & Format(Timer - t0, "0.00s")
Done:
    AppEnd
    Exit Sub
ErrH:
    LogActionSafe "ExtractFormulas", "ERR: " & Err.description & " (" & Err.Number & ")"
    Resume Done
End Sub

Private Sub ExtractFormulas_Impl()
    Dim ws As Worksheet
    Dim headerCell As Range
    Dim rateCol As Long, formCol As Long
    Dim firstDataRow As Long, lLastRow As Long
    Dim srcRng As Range, arrF As Variant, arrOut() As String
    Dim r As Long, nRows As Long

    For Each ws In ThisWorkbook.Worksheets
        If ws.Visible = xlSheetVisible And UCase(ws.Name) <> EXCLUDE_SHEET1 And _
           UCase(ws.Name) <> EXCLUDE_SHEET2 And UCase(ws.Name) <> EXCLUDE_SHEET3 Then

            Set headerCell = SafeFind(ws, HDR_RATE, True)
            If headerCell Is Nothing Then GoTo NextWs

            rateCol = headerCell.Column
            firstDataRow = headerCell.Row + 1
            lLastRow = lastDataRow(ws, rateCol)
            If lLastRow < firstDataRow Then GoTo NextWs

            formCol = rateCol + 1
            If ws.Cells(headerCell.Row, formCol).Value2 <> HDR_FORM Then
                ws.Columns(formCol).Insert Shift:=xlToRight
                ws.Cells(headerCell.Row, formCol).Value2 = HDR_FORM
                ws.Cells(headerCell.Row, formCol).Font.Bold = True
            End If

            With ws.Range(ws.Cells(firstDataRow, formCol), ws.Cells(lLastRow, formCol))
                .NumberFormat = "@"
                .ClearContents
            End With

            Set srcRng = ws.Range(ws.Cells(firstDataRow, rateCol), ws.Cells(lLastRow, rateCol))
            If srcRng.Rows.Count = 1 Then
                ReDim arrF(1 To 1, 1 To 1)
                arrF(1, 1) = srcRng.formula
            Else
                arrF = srcRng.formula
            End If
            
            nRows = UBound(arrF, 1)
            ReDim arrOut(1 To nRows, 1 To 1)

            For r = 1 To nRows
                If Len(CStr(arrF(r, 1))) > 1 Then
                    If Left$(CStr(arrF(r, 1)), 1) = "=" Then
                        arrOut(r, 1) = "'" & CStr(arrF(r, 1))
                    Else
                        arrOut(r, 1) = vbNullString
                    End If
                End If
            Next r

            ws.Range(ws.Cells(firstDataRow, formCol), ws.Cells(lLastRow, formCol)).Value = arrOut
        End If
NextWs:
    Next ws
End Sub

