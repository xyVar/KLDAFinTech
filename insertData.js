const query = `
    INSERT INTO public.market_data (asset, price)
    VALUES ($1, $2)
    RETURNING *;
`;
