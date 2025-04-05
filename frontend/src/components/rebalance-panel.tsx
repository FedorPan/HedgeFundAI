"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"

interface RebalancePanelProps {
  lastRebalance: string;
}

export default function RebalancePanel({ lastRebalance }: RebalancePanelProps) {
  const [isRebalancing, setIsRebalancing] = useState<boolean>(false);
  const [showConfirm, setShowConfirm] = useState<boolean>(false);
  
  const handleRebalanceClick = () => {
    setShowConfirm(true);
  };
  
  const handleConfirmRebalance = () => {
    setIsRebalancing(true);
    setShowConfirm(false);
    
    // Simulate API call for rebalancing
    setTimeout(() => {
      setIsRebalancing(false);
      // In a real app, would update the last rebalance time
    }, 2000);
  };
  
  const handleCancelRebalance = () => {
    setShowConfirm(false);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Rebalance</CardTitle>
        <CardDescription>
          Last rebalance: {lastRebalance}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {showConfirm ? (
          <div className="space-y-3">
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-md text-amber-800 text-sm">
              Are you sure you want to rebalance the portfolio? This will place orders to align with the target allocation.
            </div>
            <div className="flex space-x-2">
              <Button onClick={handleConfirmRebalance} className="flex-1">
                Confirm Rebalance
              </Button>
              <Button variant="outline" onClick={handleCancelRebalance} className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button 
            className="w-full"
            onClick={handleRebalanceClick}
            disabled={isRebalancing}
          >
            {isRebalancing ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Rebalancing...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Rebalance Now
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}