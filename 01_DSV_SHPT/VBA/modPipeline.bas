Attribute VB_Name = "modPipeline"
Option Explicit
'==========================
' Module: modPipeline (최종 재구성 버전)
'==========================

Public Sub START_PIPELINE()
    RunPipeline_Final
End Sub

Public Sub RunPipeline_Final(Optional ByVal ShowMsg As Boolean = True)
    Dim t0 As Single: t0 = Timer
    AppBegin "Final Pipeline"
    On Error GoTo ErrH
    LogActionSafe "PIPELINE", "START"

    ' 1단계: Formula 추출
    SafeRun "ExtractFormulasWithExclusion"
    
    ' 2단계: REV RATE 등 계산
    SafeRun "ApplyFormula_ByDynamicRemark_ExactTotal_Safe"
    
    ' 3단계: 최종 취합
    SafeRun "CompileAllSheets"

Done:
    LogActionSafe "PIPELINE", "END " & Format(Timer - t0, "0.00s")
    AppEnd
    If ShowMsg Then MsgBox "모든 파이프라인 작업 완료!", vbInformation, "Pipeline Complete"
    Exit Sub

ErrH:
    LogActionSafe "PIPELINE", "FATAL ERR: " & Err.description & " (" & Err.Number & ")"
    AppEnd
    If ShowMsg Then MsgBox "파이프라인 중단: " & vbCrLf & Err.description, vbCritical, "Pipeline Error"
End Sub

Private Sub SafeRun(ByVal ProcName As String)
    On Error GoTo ErrH
    
    If Not ProcExists(ProcName) Then
        Err.Raise 10001, , "프로시저 없음: " & ProcName
    End If

    Application.StatusBar = "Running: " & ProcName & " ..."
    Application.Run ProcName
    LogActionSafe ProcName, "OK"
    Exit Sub

ErrH:
    ' SafeRun에서 오류 발생 시, 상위 프로시저(RunPipeline_Final)의 오류 처리기로 넘김
    Err.Raise Err.Number, "Error in " & ProcName, Err.description
End Sub
