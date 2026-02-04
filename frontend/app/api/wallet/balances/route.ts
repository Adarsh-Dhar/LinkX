import { NextResponse } from "next/server";
import { ethers } from "ethers";
import { etherlinkShadownet } from "thirdweb/chains";

const DEFAULT_WXTZ_ADDRESS = "0x9D8166D4B4ac353B0269655E55cB137000ba8624"; // WXTZ (deployed)
const DEFAULT_TEST_WXTZ_ADDRESS = "0x59dfaed9a27d853ff3f2398be76da62dc50c35d7"; // TestWXTZ (legacy)
const DEFAULT_USDC_ADDRESS = "0xD2BE74974d5A50C2C131C9A0E9751c9449dc9888"; // Test USDC
const ERC20_ABI = [
  "function balanceOf(address account) view returns (uint256)",
  "function decimals() view returns (uint8)",
];

export async function GET() {
  try {
    const privateKey = process.env.WALLET_PRIVATE_KEY;
    if (!privateKey) {
      return NextResponse.json({ error: "WALLET_PRIVATE_KEY not set" }, { status: 500 });
    }

    const signer = new ethers.Wallet(privateKey);
    const walletAddress = signer.address;

    const envRpcUrl = process.env.RPC_URL || process.env.ETHERLINK_RPC_URL || process.env.NEXT_PUBLIC_ETHERLINK_RPC_URL;
    let rpcUrl = envRpcUrl || (Array.isArray(etherlinkShadownet.rpc)
      ? etherlinkShadownet.rpc[0]
      : etherlinkShadownet.rpc);

    const clientId = process.env.THIRDWEB_CLIENT_ID;
    if (clientId && rpcUrl.includes("thirdweb.com")) {
      const separator = rpcUrl.includes("?") ? "&" : "?";
      rpcUrl = `${rpcUrl}${separator}clientId=${clientId}`;
    }
    // Don't specify chainId - let ethers detect it from the RPC
    const provider = new ethers.JsonRpcProvider(rpcUrl);

    // Use checksummed addresses from ethers.getAddress() for proper EIP55 validation
    const wxtzAddress = ethers.getAddress(process.env.NEXT_PUBLIC_WXTZ_ADDRESS || process.env.WXTZ_ADDRESS || DEFAULT_WXTZ_ADDRESS);
    const testWxtzAddress = ethers.getAddress(process.env.TEST_WXTZ_ADDRESS || DEFAULT_TEST_WXTZ_ADDRESS);
    const usdcAddress = ethers.getAddress(process.env.NEXT_PUBLIC_USDC_CONTRACT || process.env.USDC_CONTRACT || DEFAULT_USDC_ADDRESS);

    const wxtzContract = new ethers.Contract(wxtzAddress, ERC20_ABI, provider);
    const testWxtzContract = new ethers.Contract(testWxtzAddress, ERC20_ABI, provider);
    const usdcContract = new ethers.Contract(usdcAddress, ERC20_ABI, provider);

    const safeDecimals = async (contract: ethers.Contract, fallback: number) => {
      try {
        return await contract.decimals();
      } catch (err) {
        console.warn(`Failed to get decimals for ${await contract.getAddress()}:`, err);
        return fallback;
      }
    };

    const safeBalance = async (contract: ethers.Contract, address: string) => {
      try {
        return await contract.balanceOf(address);
      } catch (err) {
        console.warn(`Failed to get balance of ${address} for ${await contract.getAddress()}:`, err);
        return 0n;
      }
    };

    const [
      wxtzBalanceRaw,
      wxtzDecimals,
      testWxtzBalanceRaw,
      testWxtzDecimals,
      usdcBalanceRaw,
      usdcDecimals,
    ] = await Promise.all([
      safeBalance(wxtzContract, walletAddress),
      safeDecimals(wxtzContract, 18),
      safeBalance(testWxtzContract, walletAddress),
      safeDecimals(testWxtzContract, 18),
      safeBalance(usdcContract, walletAddress),
      safeDecimals(usdcContract, 6),
    ]);

    const wxtzBalance =
      parseFloat(ethers.formatUnits(wxtzBalanceRaw, wxtzDecimals)) +
      parseFloat(ethers.formatUnits(testWxtzBalanceRaw, testWxtzDecimals));
    const usdcBalance = parseFloat(ethers.formatUnits(usdcBalanceRaw, usdcDecimals));

    return NextResponse.json({
      address: walletAddress,
      wxtzBalance,
      usdcBalance,
      tokens: {
        wxtz: wxtzAddress,
        testWxtz: testWxtzAddress,
        usdc: usdcAddress,
      }
    });
  } catch (error) {
    console.error("Wallet balances API error:", error);
    return NextResponse.json({ error: "Failed to fetch wallet balances", details: String(error) }, { status: 500 });
  }
}
