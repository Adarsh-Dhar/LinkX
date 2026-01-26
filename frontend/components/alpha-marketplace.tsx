"use client";

// ...existing code...
// This component previously displayed AlphaNode marketplace UI.
// All node-related logic and UI have been removed as requested.

export default function AlphaMarketplace() {
  return (
    <div style={{ padding: 32, textAlign: 'center' }}>
      <h2>Marketplace Unavailable</h2>
      <p>All node-related features have been removed.</p>
    </div>
  );
}
  useEffect(() => {
    async function fetchMarket() {
      try {
        const res = await fetch("/api/market/nodes");
        if (res.ok) {
          const data = await res.json();
          setNodes(data);
        } else {
          console.error("Failed to fetch nodes");
        }
      } catch (e) {
        console.error("Market offline", e);
      } finally {
        setLoading(false);
      }
    }
    fetchMarket();
  }, []);

  // 2. Handle Purchase Action
  const handlePurchase = async (nodeId: string, nodeName: string) => {
    setPurchasing(nodeId);
    try {
      const res = await fetch("/api/market/nodes", {
        method: "POST",
        body: JSON.stringify({ nodeId }),
      });

      if (res.ok) {
        // Update local state immediately
        setNodes(nodes.map(n => n.id === nodeId ? { ...n, isPurchased: true } : n));
        toast({
          title: "Access Granted",
          description: `Successfully subscribed to ${nodeName} feed.`,
        });
      }
    } catch (error) {
      toast({
        title: "Purchase Failed",
        description: "Could not verify transaction on Cronos.",
        variant: "destructive"
      });
    } finally {
      setPurchasing(null);
    }
  };

  // 3. Filter Logic
  const filteredNodes = nodes.filter(n => 
    n.name.toLowerCase().includes(search.toLowerCase()) ||
    n.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Alpha Node Market</h2>
          <p className="text-muted-foreground">
            Acquire high-value data streams via the x402 Protocol.
          </p>
        </div>
        <div className="flex w-full max-w-sm items-center space-x-2 bg-zinc-900/50 p-1 rounded-lg border border-zinc-800">
          <Search className="h-4 w-4 ml-2 text-zinc-500" />
          <Input 
            placeholder="Search providers..." 
            className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Grid Content */}
      <div className="flex-1 overflow-y-auto pr-2">
        {loading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-[280px] w-full rounded-xl bg-zinc-900" />
            ))}
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 pb-10">
            {filteredNodes.map((node) => {
              const IconComponent = IconMap[node.icon] || Activity;
              const isOwned = node.isPurchased;

              return (
                <Card 
                  key={node.id} 
                  className={`flex flex-col border-zinc-800 transition-all duration-200 ${isOwned ? 'bg-zinc-900/30' : 'bg-black hover:border-zinc-600'}`}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="outline" className={`
                        ${node.category === 'Sentiment' ? 'border-purple-500/50 text-purple-400' : ''}
                        ${node.category === 'On-Chain' ? 'border-blue-500/50 text-blue-400' : ''}
                        ${node.category === 'Technical' ? 'border-orange-500/50 text-orange-400' : ''}
                      `}>
                        {node.category}
                      </Badge>
                      <div className="flex items-center gap-1.5">
                        <div className={`h-1.5 w-1.5 rounded-full ${node.status === 'active' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-red-500'}`} />
                        <span className="text-[10px] uppercase text-muted-foreground">{node.status}</span>
                      </div>
                    </div>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <IconComponent className={`h-5 w-5 ${isOwned ? 'text-green-500' : 'text-zinc-400'}`} />
                      {node.name}
                    </CardTitle>
                  </CardHeader>
                  
                  <CardContent className="flex-1">
                    <CardDescription className="line-clamp-3 mb-4 min-h-[60px]">
                      {node.description}
                    </CardDescription>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-zinc-900/50 p-2 rounded border border-zinc-800">
                        <span className="block text-zinc-500 mb-1">Reputation</span>
                        <span className="font-mono text-green-400">{node.reputation}/100</span>
                      </div>
                      <div className="bg-zinc-900/50 p-2 rounded border border-zinc-800">
                        <span className="block text-zinc-500 mb-1">Update Rate</span>
                        <span className="font-mono text-white">~200ms</span>
                      </div>
                    </div>
                  </CardContent>

                  <CardFooter className="pt-2">
                    <Button 
                      className={`w-full transition-all ${isOwned 
                        ? "bg-green-900/20 text-green-400 border-green-900/50 hover:bg-green-900/30" 
                        : "bg-white text-black hover:bg-zinc-200"}`}
                      variant={isOwned ? "outline" : "default"}
                      disabled={isOwned || purchasing === node.id}
                      onClick={() => handlePurchase(node.id, node.name)}
                    >
                      {isOwned ? (
                        <>
                          <Check className="mr-2 h-4 w-4" /> Active
                        </>
                      ) : (
                        <>
                          {purchasing === node.id ? (
                            <Activity className="mr-2 h-4 w-4 animate-spin" /> 
                          ) : (
                            <ShoppingCart className="mr-2 h-4 w-4" />
                          )}
                          Buy ${node.price.toFixed(2)}
                        </>
                      )}
                    </Button>
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
