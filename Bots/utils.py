import os
import httpx
from dotenv import load_dotenv
from web3 import HTTPProvider, Web3

load_dotenv()

# Web3 setup
MAINNET_HTTP_RPC_URL = os.getenv("MAINNET_HTTP_RPC_URL")

# ERC20 ABI for totalSupply function
ERC20_TOTAL_SUPPLY_ABI = """[{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]"""

# Token addresses
TOKEN_ADDRESSES = {
    "ASF": "0x59a529070fbb61e6d6c91f952ccb7f35c34cf8aa",
    "USDAF": "0x85E30b8b263bC64d94b827ed450F2EdFEE8579dA",
}

# Coingecko IDs for Defillama API
COINGECKO_IDS = {
    "ASF": "asymmetry-finance",
    "USDAF": "asymmetry-usdaf",
}


def get_web3_instance():
    """Get a Web3 instance connected to mainnet"""
    # List of public Ethereum RPC endpoints
    public_rpcs = [
        "https://rpc.ankr.com/eth",
        "https://eth-mainnet.public.blastapi.io",
        "https://ethereum.publicnode.com",
        "https://1rpc.io/eth",
        "https://eth.llamarpc.com"
    ]

    # Try environment variable first if set
    if MAINNET_HTTP_RPC_URL:
        public_rpcs.insert(0, MAINNET_HTTP_RPC_URL)

    # Try each RPC until one works
    for rpc_url in public_rpcs:
        try:
            w3 = Web3(HTTPProvider(rpc_url))
            if w3.is_connected():
                return w3
        except Exception:
            continue

    raise Exception("Could not connect to any Ethereum RPC endpoint")


def format_large_number(value: float) -> str:
    """Format large numbers with appropriate suffixes (K, M, B, T)"""
    if value >= 1_000_000_000_000:  # Trillion
        return f"${value / 1_000_000_000_000:.2f}T"
    elif value >= 1_000_000_000:  # Billion
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:  # Million
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:  # Thousand
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"


def fetch_token_price(token_symbol: str, search_width: str = "4h") -> float:
    """
    Fetch token price from Defillama API
    
    Args:
        token_symbol: Token symbol (e.g., "ASF", "USDAF")
        search_width: Time window for price search (default: "4h")
    
    Returns:
        Token price as float
    """
    coingecko_id = COINGECKO_IDS.get(token_symbol.upper())
    if not coingecko_id:
        raise ValueError(f"Unknown token symbol: {token_symbol}")

    res = httpx.get(
        f"https://coins.llama.fi/prices/current/coingecko:{coingecko_id}?searchWidth={search_width}"
    )
    data = res.json()
    price = data["coins"][f"coingecko:{coingecko_id}"]["price"]

    return price


def fetch_token_supply(token_symbol: str, decimals: int = 18) -> float:
    """
    Fetch token total supply from blockchain
    
    Args:
        token_symbol: Token symbol (e.g., "ASF", "USDAF")
        decimals: Token decimals (default: 18)
    
    Returns:
        Token total supply as float
    """
    token_address = TOKEN_ADDRESSES.get(token_symbol.upper())
    if not token_address:
        raise ValueError(f"Unknown token symbol: {token_symbol}")

    w3 = get_web3_instance()
    # Convert to checksum address
    token_address = w3.to_checksum_address(token_address)
    contract = w3.eth.contract(address=token_address, abi=ERC20_TOTAL_SUPPLY_ABI)
    supply = contract.functions.totalSupply().call() / (10 ** decimals)

    return supply


def calculate_market_cap(token_symbol: str, use_circulating: bool = True) -> float:
    """
    Calculate market cap for a token with fallback strategy:
    1. Try DefiLlama (doesn't have mcap data currently, but checking for future)
    2. Try CoinGecko for circulating supply market cap
    3. Fallback to price * total supply from blockchain
    
    Args:
        token_symbol: Token symbol (e.g., "ASF", "USDAF")
        use_circulating: If True, attempts to use circulating supply from APIs
    
    Returns:
        Market cap as float
    """

    if use_circulating:
        coingecko_id = COINGECKO_IDS.get(token_symbol.upper())

        if coingecko_id:
            # 1. First try DefiLlama (in case they add mcap data in future)
            try:
                res = httpx.get(
                    f"https://coins.llama.fi/prices/current/coingecko:{coingecko_id}",
                    params={"searchWidth": "4h", "includeMcap": "true"}
                )
                data = res.json()
                coin_data = data.get("coins", {}).get(f"coingecko:{coingecko_id}", {})

                # If DefiLlama starts providing mcap, use it
                if "mcap" in coin_data and coin_data["mcap"]:
                    print(f"Using DefiLlama mcap: ${coin_data['mcap']:,.0f}")

                    return coin_data["mcap"]
            except Exception:
                pass

            # 2. Try CoinGecko as fallback
            try:
                res = httpx.get(
                    f"https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": coingecko_id,
                        "vs_currencies": "usd",
                        "include_market_cap": "true"
                    },
                    timeout=5.0  # Add timeout to prevent hanging
                )
                data = res.json()

                if coingecko_id in data and "usd_market_cap" in data[coingecko_id]:
                    mcap = data[coingecko_id]["usd_market_cap"]
                    # Only return if market cap is non-zero
                    if mcap > 0:
                        return mcap
            except Exception:
                pass

    # 3. Final fallback: calculate from price * total supply
    price = fetch_token_price(token_symbol)
    supply = fetch_token_supply(token_symbol)

    return price * supply


def fetch_protocol_tvl(protocol_name: str) -> float:
    """
    Fetch protocol TVL from Defillama API
    
    Args:
        protocol_name: Protocol name (e.g., "asymmetry-usdaf")
    
    Returns:
        TVL as float
    """
    res = httpx.get(f"https://api.llama.fi/tvl/{protocol_name}")

    return res.json()
