Attribute VB_Name = "modCompileMaster"
Option Explicit

'================================================================
' Module: modCompileMaster
' Purpose: 모든 시트를 순회하며 '데이터 행'만 필터링하여 마스터 시트에 취합
'================================================================

'--- 메인 실행 프로시저 ---
Public Sub CompileAllSheets()
    Dim t0 As Single: t0 = Timer
    
    '--- 1. 환경 설정 및 출력 시트 준비 ---
    On Error GoTo ErrH
    Application.ScreenUpdating = False
    
    Dim outWS As Worksheet
    On Error Resume Next
    Set outWS = ThisWorkbook.Worksheets("MasterData")
    If outWS Is Nothing Then
        Set outWS = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        outWS.Name = "MasterData"
    End If
    On Error GoTo ErrH
    outWS.Cells.Clear
    
    '--- 2. 마스터 시트에 헤더 작성 ---
    Dim headers As Variant
    headers = Array("CWI Job Number", "Order Ref. Number", "S/No", "RATE SOURCE", "DESCRIPTION", "RATE", "Formula", "Q'TY", "TOTAL (USD)", "REMARK", "REV RATE", "REV TOTAL", "DIFFERENCE")
    outWS.Range("A1").Resize(1, UBound(headers) + 1).Value = headers
    outWS.Rows(1).Font.Bold = True
    
    '--- 3. 모든 시트를 순회하며 데이터 추출 ---
    Dim ws As Worksheet
    Dim writeRow As Long: writeRow = 2
    
    For Each ws In ThisWorkbook.Worksheets
        ' 마스터 시트이거나 숨겨진 시트는 건너뛰기
        If ws.Name <> outWS.Name And ws.Visible = xlSheetVisible Then
            
            '--- 4. 시트 상단의 헤더 정보 추출 ---
            Dim jobNum As String, orderRef As String
            jobNum = GetValueFromLabel(ws, "CW1 Job Number")
            orderRef = GetValueFromLabel(ws, "Order Ref. Number")
            
            '--- 5. [로직 변경] 시트의 모든 행을 검사하여 데이터 행만 추출 ---
            Dim firstHeaderRow As Long, lastUsedRow As Long
            Dim snCol As Long, lastCol As Long
            Dim r As Long
            
            ' S/No 헤더를 찾아 기준 열로 설정
            firstHeaderRow = FindHeaderRow(ws, "S/No")
            If firstHeaderRow > 0 Then
                snCol = FindCol(ws, firstHeaderRow, "S/No")
                lastCol = ws.Cells(firstHeaderRow, ws.Columns.Count).End(xlToLeft).Column
                lastUsedRow = ws.Cells(ws.Rows.Count, snCol).End(xlUp).Row
                
                ' 헤더 아래부터 마지막 사용된 행까지 순회
                For r = firstHeaderRow + 1 To lastUsedRow
                    ' S/No 열에 숫자가 있는 행만 데이터 행으로 간주
                    If IsNumeric(ws.Cells(r, snCol).Value) And Not IsEmpty(ws.Cells(r, snCol).Value) Then
                        ' 헤더 정보 쓰기
                        outWS.Cells(writeRow, 1).Value = jobNum
                        outWS.Cells(writeRow, 2).Value = orderRef
                        
                        ' 데이터 행 전체 복사
                        ws.Range(ws.Cells(r, snCol), ws.Cells(r, lastCol)).Copy
                        outWS.Cells(writeRow, 3).PasteSpecial xlPasteValues
                        
                        writeRow = writeRow + 1
                    End If
                Next r
            End If
        End If
    Next ws
    
    '--- 6. 마무리 ---
    Application.CutCopyMode = False
    outWS.Columns.AutoFit
    Application.ScreenUpdating = True
    MsgBox "모든 시트의 데이터 행 취합 완료!", vbInformation, "작업 완료"
    Exit Sub

ErrH:
    Application.CutCopyMode = False
    Application.ScreenUpdating = True
    MsgBox "오류 발생: " & Err.description, vbCritical, "오류"
End Sub


'--- 보조 함수 (Helper Functions) ---

Private Function GetValueFromLabel(ws As Worksheet, labelText As String) As String
    Dim foundCell As Range
    On Error Resume Next
    Set foundCell = ws.UsedRange.Find(What:=labelText, LookIn:=xlValues, LookAt:=xlPart)
    On Error GoTo 0
    
    If Not foundCell Is Nothing Then
        GetValueFromLabel = CStr(foundCell.Offset(0, 1).Value)
    Else
        GetValueFromLabel = ""
    End If
End Function

Private Function FindHeaderRow(ws As Worksheet, headerText As String) As Long
    Dim foundCell As Range
    On Error Resume Next
    Set foundCell = ws.UsedRange.Find(What:=headerText, LookIn:=xlValues, LookAt:=xlWhole)
    On Error GoTo 0
    
    If Not foundCell Is Nothing Then
        FindHeaderRow = foundCell.Row
    Else
        FindHeaderRow = 0
    End If
End Function

Private Function FindCol(ws As Worksheet, r As Long, headerText As String) As Long
    Dim foundCell As Range
    On Error Resume Next
    Set foundCell = ws.Rows(r).Find(What:=headerText, LookIn:=xlValues, LookAt:=xlWhole)
    On Error GoTo 0
    
    If Not foundCell Is Nothing Then
        FindCol = foundCell.Column
    Else
        FindCol = 0
    End If
End Function
