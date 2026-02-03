import { NextResponse } from "next/server";
import { ethers } from "ethers";
import { etherlinkShadownet } from "thirdweb/chains";

const WXTZ_ADDRESS = "0xd0d8db4db6b24ab85a954df21c84f9d23612d552"; // WXTZ
const TEST_WXTZ_ADDRESS = "0x59dfaed9a27d853ff3f2398be76da62dc50c35d7"; // TestWXTZ
const USDC_ADDRESS = "0xd2be74974d5a50c2c131c9a0e9751c9449dc9888"; // Test USDC
const ERC20_ABI = [
  "function balanceOf(address account) view returns (uint256)",
  "function decimals() view returns (uint8)",
];

export async function GET() {
  try {
    const serverWalletAddress = process.env.WALLET_PRIVATE_KEY;
    if (!serverWalletAddress) {
      return NextResponse.json({ error: "WALLET_PRIVATE_KEY not set" }, { status: 500 });
    }

    const envRpcUrl = process.env.ETHERLINK_RPC_URL || process.env.NEXT_PUBLIC_ETHERLINK_RPC_URL;
    let rpcUrl = envRpcUrl || (Array.isArray(etherlinkShadownet.rpc)
      ? etherlinkShadownet.rpc[0]
      : etherlinkShadownet.rpc);

    const clientId = process.env.THIRDWEB_CLIENT_ID;
    if (clientId && rpcUrl.includes("thirdweb.com")) {
      const separator = rpcUrl.includes("?") ? "&" : "?";
      rpcUrl = `${rpcUrl}${separator}clientId=${clientId}`;
    }
    const provider = new ethers.JsonRpcProvider(
      rpcUrl,
      { chainId: 127823, name: "etherlink-shadownet" }
    );

    const wxtzContract = new ethers.Contract(WXTZ_ADDRESS, ERC20_ABI, provider);
    const testWxtzContract = new ethers.Contract(TEST_WXTZ_ADDRESS, ERC20_ABI, provider);
    const usdcContract = new ethers.Contract(USDC_ADDRESS, ERC20_ABI, provider);

    const safeDecimals = async (contract: ethers.Contract, fallback: number) => {
      try {
        return await contract.decimals();
      } catch {
        return fallback;
      }
    };

    const safeBalance = async (contract: ethers.Contract) => {
      try {
        return await contract.balanceOf(serverWalletAddress);
      } catch {
        return 0;
      }
    };

    const [
      wxtzBalanceRaw,
      wxtzDecimals,
      testWxtzBalanceRaw,
      testWxtzDecimals,
      usdcBalanceRaw,
    ] = await Promise.all([
      safeBalance(wxtzContract),
      safeDecimals(wxtzContract, 18),
      safeBalance(testWxtzContract),
      safeDecimals(testWxtzContract, 18),
      safeBalance(usdcContract),
    ]);

    const wxtzBalance =
      parseFloat(ethers.formatUnits(wxtzBalanceRaw, wxtzDecimals)) +
      parseFloat(ethers.formatUnits(testWxtzBalanceRaw, testWxtzDecimals));
    const usdcBalance = parseFloat(ethers.formatUnits(usdcBalanceRaw, 6));

    return NextResponse.json({
      address: serverWalletAddress,
      wxtzBalance,
      usdcBalance,
    });
  } catch (error) {
    console.error("Wallet balances API error:", error);
    return NextResponse.json({ error: "Failed to fetch wallet balances" }, { status: 500 });
  }
}
