"use client"

import { useState, useEffect } from "react"
import { ethers } from "ethers"

interface WalletState {
  address: string | null
  balance: string | null
  usdcBalance: string | null
  isConnected: boolean
  isConnecting: boolean
  chainId: number | null
}

const USDC_ADDRESS = "0x908059CF02cbb643Bc96C55e14Fb3699e632479f" // Cronos Testnet
const CRONOS_TESTNET_CHAIN_ID = 338
const USDC_ABI = [
  "function balanceOf(address account) view returns (uint256)",
  "function decimals() view returns (uint8)",
]

export function useWallet() {
  const [state, setState] = useState<WalletState>({
    address: null,
    balance: null,
    usdcBalance: null,
    isConnected: false,
    isConnecting: false,
    chainId: null,
  })

  const connect = async () => {
    // Check for MetaMask specifically
    let ethereum = window.ethereum
    
    // If multiple wallets are installed, try to get MetaMask specifically
    if (window.ethereum?.providers?.length) {
      ethereum = window.ethereum.providers.find((provider: any) => provider.isMetaMask)
    }
    
    if (!ethereum) {
      alert("Please install MetaMask to use this feature!")
      return
    }

    setState((prev) => ({ ...prev, isConnecting: true }))

    try {
      const provider = new ethers.BrowserProvider(ethereum)
      const accounts = await provider.send("eth_requestAccounts", [])
      const address = accounts[0]
      const network = await provider.getNetwork()
      const chainId = Number(network.chainId)

      // Get CRO balance
      const balance = await provider.getBalance(address)
      const balanceFormatted = ethers.formatEther(balance)

      // Get USDC balance
      let usdcBalance = "0"
      try {
        const usdcContract = new ethers.Contract(USDC_ADDRESS, USDC_ABI, provider)
        const usdcBalanceRaw = await usdcContract.balanceOf(address)
        usdcBalance = ethers.formatUnits(usdcBalanceRaw, 6) // USDC has 6 decimals
      } catch (error) {
        console.warn("Error fetching USDC balance (this is normal if contract not on chain):", error)
        usdcBalance = "0"
      }

      setState({
        address,
        balance: balanceFormatted,
        usdcBalance,
        isConnected: true,
        isConnecting: false,
        chainId,
      })

      // Check if on correct network
      if (chainId !== CRONOS_TESTNET_CHAIN_ID) {
        console.warn(
          `Connected to chain ${chainId}. Please switch to Cronos Testnet (${CRONOS_TESTNET_CHAIN_ID})`
        )
      }
    } catch (error) {
      console.error("Failed to connect wallet:", error)
      setState((prev) => ({ ...prev, isConnecting: false }))
    }
  }

  const disconnect = () => {
    setState({
      address: null,
      balance: null,
      usdcBalance: null,
      isConnected: false,
      isConnecting: false,
      chainId: null,
    })
  }

  const refreshBalances = async () => {
    if (!state.address) return
    
    // Get MetaMask provider specifically
    let ethereum = window.ethereum
    if (window.ethereum?.providers?.length) {
      ethereum = window.ethereum.providers.find((provider: any) => provider.isMetaMask)
    }
    
    if (!ethereum) return

    try {
      const provider = new ethers.BrowserProvider(ethereum)

      // Get CRO balance
      const balance = await provider.getBalance(state.address)
      const balanceFormatted = ethers.formatEther(balance)

      // Get USDC balance
      let usdcBalance = "0"
      try {
        const usdcContract = new ethers.Contract(USDC_ADDRESS, USDC_ABI, provider)
        const usdcBalanceRaw = await usdcContract.balanceOf(state.address)
        usdcBalance = ethers.formatUnits(usdcBalanceRaw, 6)
      } catch (error) {
        console.error("Error fetching USDC balance:", error)
      }

      setState((prev) => ({ ...prev, balance: balanceFormatted, usdcBalance }))
    } catch (error) {
      console.error("Failed to refresh balances:", error)
    }
  }

  // Listen for account changes
  useEffect(() => {
    // Get MetaMask provider specifically
    let ethereum = window.ethereum
    if (window.ethereum?.providers?.length) {
      ethereum = window.ethereum.providers.find((provider: any) => provider.isMetaMask)
    }
    
    if (!ethereum) return

    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        disconnect()
      } else if (accounts[0] !== state.address) {
        // Account changed, reconnect
        connect()
      }
    }

    const handleChainChanged = () => {
      // Reload the page when chain changes
      window.location.reload()
    }

    ethereum.on("accountsChanged", handleAccountsChanged)
    ethereum.on("chainChanged", handleChainChanged)

    return () => {
      ethereum.removeListener("accountsChanged", handleAccountsChanged)
      ethereum.removeListener("chainChanged", handleChainChanged)
    }
  }, [state.address])

  // Auto-connect if previously connected
  useEffect(() => {
    // Get MetaMask provider specifically
    let ethereum = window.ethereum
    if (window.ethereum?.providers?.length) {
      ethereum = window.ethereum.providers.find((provider: any) => provider.isMetaMask)
    }
    
    if (!ethereum) return

    const checkConnection = async () => {
      try {
        const provider = new ethers.BrowserProvider(ethereum)
        const accounts = await provider.send("eth_accounts", [])
        if (accounts.length > 0) {
          connect()
        }
      } catch (error) {
        console.error("Failed to check connection:", error)
      }
    }

    checkConnection()
  }, [])

  return {
    ...state,
    connect,
    disconnect,
    refreshBalances,
    shortAddress: state.address
      ? `${state.address.slice(0, 6)}...${state.address.slice(-4)}`
      : null,
  }
}
