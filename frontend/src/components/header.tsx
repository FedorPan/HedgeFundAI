"use client"

import React, { useState } from "react"
import Link from "next/link"
import { Settings, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { toast } from "@/components/ui/use-toast"

export default function Header() {
  const [isUpdating, setIsUpdating] = useState(false);

  const refreshData = async () => {
    if (isUpdating) return;
    
    setIsUpdating(true);
    toast({
      title: "Обновление данных запущено",
      description: "Пожалуйста, подождите. Это может занять несколько минут."
    });
    
    try {
      const response = await fetch('/api/proxy?endpoint=data/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast({
          title: "Обновление запущено",
          description: "Данные обновляются в фоновом режиме. Обновите страницу через несколько минут."
        });
      } else {
        toast({
          title: "Ошибка",
          description: result.message || "Не удалось запустить обновление данных",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось подключиться к серверу",
        variant: "destructive"
      });
      console.error('Error refreshing data:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <header className="border-b bg-white">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center">
          <Link href="/" className="flex items-center">
            <span className="text-2xl font-bold text-primary">HedgeFundAI</span>
          </Link>
        </div>
        
        <div className="flex items-center space-x-4">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="outline" 
                  size="icon" 
                  onClick={refreshData}
                  disabled={isUpdating}
                >
                  <RefreshCw className={`h-5 w-5 ${isUpdating ? 'animate-spin' : ''}`} />
                  <span className="sr-only">Обновить данные</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Обновить данные (раз в неделю)</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
            <span className="sr-only">Settings</span>
          </Button>
        </div>
      </div>
    </header>
  )
}