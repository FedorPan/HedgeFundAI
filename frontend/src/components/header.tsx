"use client"

import React from "react"
import Link from "next/link"
import { Settings } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function Header() {
  return (
    <header className="border-b bg-white">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center">
          <Link href="/" className="flex items-center">
            <span className="text-2xl font-bold text-primary">HedgeFundAI</span>
          </Link>
        </div>
        
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
            <span className="sr-only">Settings</span>
          </Button>
        </div>
      </div>
    </header>
  )
}