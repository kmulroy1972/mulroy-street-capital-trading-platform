'use client'

import { useState, useEffect } from 'react'
import LoginGate from '@/components/auth/LoginGate'

function AdminPanelContent() {
  const [changeRequest, setChangeRequest] = useState('')
  const [changeType, setChangeType] = useState('custom')
  const [activityLog, setActivityLog] = useState<string[]>([])
  const [changeQueue, setChangeQueue] = useState<any[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const addLog = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
    const timestamp = new Date().toLocaleTimeString()
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : '📝'
    setActivityLog(prev => [
      `[${timestamp}] ${prefix} ${message}`,
      ...prev.slice(0, 49)
    ])
  }
  
  // Fetch change queue periodically
  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const res = await fetch('https://mulroystreetcap.com/api/admin/change-queue')
        const data = await res.json()
        if (data.success) {
          // Sanitize the queue data to handle null execution_log
          const sanitizedQueue = (data.queue || []).map(change => ({
            ...change,
            execution_log: change.execution_log || []
          }))
          setChangeQueue(sanitizedQueue)
        }
      } catch (error) {
        console.error('Failed to fetch queue:', error)
      }
    }
    
    fetchQueue()
    const interval = setInterval(fetchQueue, 5000) // Every 5 seconds
    return () => clearInterval(interval)
  }, [])
  
  const handleSubmitChange = async () => {
    if (!changeRequest) {
      addLog('Please enter a change description', 'error')
      return
    }
    
    setIsSubmitting(true)
    addLog(`Submitting: ${changeRequest}`, 'info')
    console.log('Starting submission to:', 'https://mulroystreetcap.com/api/admin/change-request')
    
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const response = await fetch('https://mulroystreetcap.com/api/admin/change-request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: changeRequest,
          type: changeType,
          timestamp: new Date().toISOString()
        }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      
      if (result.success) {
        addLog(`Change queued! ID: ${result.id}`, 'success')
        addLog(result.instruction, 'info')
        
        // Clear form
        setChangeRequest('')
        setChangeType('custom')
        
        // Refresh queue
        const queueRes = await fetch('https://mulroystreetcap.com/api/admin/change-queue')
        const queueData = await queueRes.json()
        if (queueData.success) {
          const sanitizedQueue = (queueData.queue || []).map(change => ({
            ...change,
            execution_log: change.execution_log || []
          }))
          setChangeQueue(sanitizedQueue)
        }
      } else {
        addLog(`Failed: ${result.error}`, 'error')
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        addLog('Request timeout - please try again', 'error')
      } else {
        addLog(`Error: ${error}`, 'error')
      }
    } finally {
      setIsSubmitting(false)
    }
  }
  
  const handleExecuteChange = async (changeId: number, isAutoExecute = false) => {
    const action = isAutoExecute ? 'Auto-executing' : 'Preparing'
    addLog(`${action} change ${changeId}...`, 'info')
    
    try {
      const endpoint = isAutoExecute 
        ? `https://mulroystreetcap.com/api/admin/auto-execute-change/${changeId}`
        : `https://mulroystreetcap.com/api/admin/execute-change/${changeId}`
      
      const response = await fetch(endpoint, {
        method: 'POST'
      })
      
      const result = await response.json()
      
      if (result.success) {
        addLog(result.message, 'success')
        if (result.instruction) addLog(result.instruction, 'info')
        
        // Refresh the queue to show updated status
        const queueRes = await fetch('https://mulroystreetcap.com/api/admin/change-queue')
        const queueData = await queueRes.json()
        if (queueData.success) {
          const sanitizedQueue = (queueData.queue || []).map(change => ({
            ...change,
            execution_log: change.execution_log || []
          }))
          setChangeQueue(sanitizedQueue)
        }
      } else {
        addLog(`Failed: ${result.error}`, 'error')
      }
    } catch (error) {
      addLog(`Error: ${error}`, 'error')
    }
  }

  const handleAutoExecuteSimple = async () => {
    const simpleChanges = changeQueue.filter(change => 
      change.status === 'script_created' && 
      (change.description.toLowerCase().includes('remove') || 
       change.description.toLowerCase().includes('color') ||
       change.description.toLowerCase().includes('text'))
    )
    
    if (simpleChanges.length === 0) {
      addLog('No simple changes ready for auto-execution', 'info')
      return
    }
    
    addLog(`Auto-executing ${simpleChanges.length} simple changes...`, 'info')
    
    for (const change of simpleChanges) {
      await handleExecuteChange(change.id, true)
      // Small delay between executions
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }
  
  const handleLogout = () => {
    if ((window as any).mscLogout) {
      (window as any).mscLogout()
      window.location.href = '/'
    }
  }
  
  const baseStyles = {
    container: {
      minHeight: '100vh',
      backgroundColor: '#0A0E1A',
      color: '#E4E7EB',
      fontFamily: 'SF Mono, Monaco, monospace'
    },
    header: {
      backgroundColor: '#050810',
      borderBottom: '1px solid #2D3748',
      padding: '16px 24px',
      display: 'flex' as const,
      justifyContent: 'space-between' as const,
      alignItems: 'center' as const
    },
    card: {
      backgroundColor: '#141824',
      border: '1px solid #2D3748',
      borderRadius: '2px',
      padding: '20px',
      marginBottom: '20px'
    },
    button: {
      padding: '10px 20px',
      border: 'none',
      borderRadius: '2px',
      cursor: 'pointer',
      fontSize: '12px',
      fontWeight: 'bold' as const,
      letterSpacing: '0.5px',
      textTransform: 'uppercase' as const,
      transition: 'all 0.2s'
    }
  }
  
  return (
    <div style={baseStyles.container}>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
      {/* Header */}
      <div style={baseStyles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <h1 style={{ color: '#FF6B35', fontSize: '20px', fontWeight: 'bold' }}>
            MSC ADMIN PANEL
          </h1>
          <span style={{ color: '#00FF88', fontSize: '10px' }}>
            ● API CONNECTED
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => window.open('/', '_blank')}
            style={{ ...baseStyles.button, backgroundColor: '#2563eb', color: 'white' }}
          >
            View Dashboard
          </button>
          <button
            onClick={handleLogout}
            style={{ ...baseStyles.button, backgroundColor: '#333', color: '#AAA' }}
          >
            Logout
          </button>
        </div>
      </div>
      
      <div style={{ padding: '24px' }}>
        {/* Change Request Form */}
        <div style={baseStyles.card}>
          <h2 style={{ fontSize: '14px', marginBottom: '16px', color: '#A0A9B8' }}>
            SUBMIT DASHBOARD CHANGE
          </h2>
          
          <select
            value={changeType}
            onChange={(e) => {
              setChangeType(e.target.value)
              if (e.target.value !== 'custom') {
                setChangeRequest(e.target.value)
              }
            }}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#0A0E1A',
              border: '1px solid #2D3748',
              color: '#E4E7EB',
              borderRadius: '2px',
              marginBottom: '12px'
            }}
          >
            <option value="custom">Custom Change Request</option>
            <option value="Remove weather widget from header">Remove Weather Widget</option>
            <option value="Add portfolio performance chart">Add Performance Chart</option>
            <option value="Change header color to blue">Change Header Color</option>
            <option value="Add new metric card for total P&L">Add Total P&L Card</option>
            <option value="Increase all font sizes by 2px">Increase Font Sizes</option>
            <option value="Add dark/light mode toggle">Add Theme Toggle</option>
          </select>
          
          <textarea
            value={changeRequest}
            onChange={(e) => setChangeRequest(e.target.value)}
            placeholder="Describe your change in detail..."
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: '#0A0E1A',
              border: '1px solid #2D3748',
              color: '#E4E7EB',
              borderRadius: '2px',
              minHeight: '100px',
              marginBottom: '12px'
            }}
          />
          
          <button
            onClick={handleSubmitChange}
            disabled={isSubmitting}
            style={{
              ...baseStyles.button,
              backgroundColor: isSubmitting ? '#666' : '#FF6B35',
              color: 'white'
            }}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Change Request'}
          </button>
        </div>
        
        {/* Change Queue */}
        <div style={baseStyles.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '14px', color: '#A0A9B8' }}>
              CHANGE QUEUE ({changeQueue.length})
            </h2>
            <button
              onClick={handleAutoExecuteSimple}
              disabled={changeQueue.filter(c => c.status === 'script_created').length === 0}
              style={{
                ...baseStyles.button,
                padding: '6px 12px',
                fontSize: '10px',
                backgroundColor: changeQueue.filter(c => c.status === 'script_created').length > 0 ? '#9333ea' : '#666',
                color: 'white'
              }}
            >
              Auto-Execute Simple
            </button>
          </div>
          
          <div style={{ maxHeight: '200px', overflow: 'auto' }}>
            {changeQueue.length === 0 ? (
              <div style={{ color: '#6B7280', fontSize: '12px' }}>No pending changes</div>
            ) : (
              changeQueue.map((change) => (
                <div key={change.id} style={{
                  backgroundColor: '#0A0E1A',
                  border: '1px solid #2D3748',
                  padding: '12px',
                  marginBottom: '8px',
                  borderRadius: '2px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '12px', color: '#A0A9B8' }}>
                        #{change.id} - {new Date(change.timestamp).toLocaleString()}
                      </div>
                      <div style={{ fontSize: '13px', marginTop: '4px' }}>
                        {change.description}
                      </div>
                      <div style={{
                        fontSize: '11px',
                        marginTop: '4px',
                        color: change.status === 'pending' ? '#FFB800' :
                               change.status === 'script_created' ? '#00FF88' :
                               change.status === 'executing' ? '#2563eb' :
                               change.status === 'completed' ? '#00FF88' : 
                               change.status === 'failed' ? '#FF3366' : '#FFB800',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        {change.status === 'executing' && (
                          <span style={{ animation: 'spin 1s linear infinite' }}>⚡</span>
                        )}
                        Status: {change.status === 'script_created' ? 'READY' : 
                                change.status === 'executing' ? 'EXECUTING...' :
                                change.status.toUpperCase()}
                      </div>
                    </div>
                    {change.status === 'pending' && (
                      <button
                        onClick={() => handleExecuteChange(change.id)}
                        style={{
                          ...baseStyles.button,
                          padding: '6px 12px',
                          fontSize: '10px',
                          backgroundColor: '#059669',
                          color: 'white'
                        }}
                      >
                        Prepare
                      </button>
                    )}
                    {(change.status === 'script_created' || (change.status === 'failed' && change.script_path)) && (
                      <button
                        onClick={() => handleExecuteChange(change.id)}
                        style={{
                          ...baseStyles.button,
                          padding: '6px 12px',
                          fontSize: '10px',
                          backgroundColor: change.status === 'failed' ? '#dc2626' : '#00FF88',
                          color: change.status === 'failed' ? 'white' : '#0A0E1A'
                        }}
                      >
                        {change.status === 'failed' ? 'RETRY' : 'EXECUTE'}
                      </button>
                    )}
                    {change.status === 'executing' && (
                      <div style={{
                        padding: '6px 12px',
                        fontSize: '10px',
                        backgroundColor: '#2563eb',
                        color: 'white',
                        borderRadius: '2px',
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <span style={{ animation: 'spin 1s linear infinite' }}>⚡</span>
                        RUNNING
                      </div>
                    )}
                    {change.status === 'completed' && (
                      <div style={{
                        padding: '6px 12px',
                        fontSize: '10px',
                        backgroundColor: '#059669',
                        color: 'white',
                        borderRadius: '2px',
                        fontWeight: 'bold'
                      }}>
                        ✅ DONE
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
        {/* Activity Log */}
        <div style={baseStyles.card}>
          <h2 style={{ fontSize: '14px', marginBottom: '16px', color: '#A0A9B8' }}>
            ACTIVITY LOG
          </h2>
          
          <div style={{
            backgroundColor: '#0A0E1A',
            padding: '12px',
            height: '200px',
            overflow: 'auto',
            fontSize: '11px',
            fontFamily: 'monospace'
          }}>
            {activityLog.length === 0 ? (
              <div style={{ color: '#6B7280' }}>No activity logged...</div>
            ) : (
              activityLog.map((log, i) => (
                <div key={i} style={{ color: '#00FF88', marginBottom: '4px' }}>
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AdminPanel() {
  return (
    <LoginGate pageName="Admin Panel">
      <AdminPanelContent />
    </LoginGate>
  )
}