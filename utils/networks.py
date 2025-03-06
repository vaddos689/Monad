class Network:
    def __init__(
            self,
            name: str,
            rpc: list,
            chain_id: int,
            eip1559_support: bool,
            token: str,
            explorer: str,
            decimals: int = 18
    ):
        self.name = name
        self.rpc = rpc
        self.chain_id = chain_id
        self.eip1559_support = eip1559_support
        self.token = token
        self.explorer = explorer
        self.decimals = decimals

    def __repr__(self):
        return f'{self.name}'

MonadRPC = Network(
    name='Monad Testnet',
    rpc=[
        'https://testnet-rpc.monad.xyz/'
    ],
    chain_id=10143,
    eip1559_support=True,
    token='MON',
    explorer='https://testnet.monadexplorer.com/'
)