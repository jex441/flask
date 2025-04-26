import { useState } from "react";
import "./App.css";

function App() {
	return (
		<main className="h-[500px] w-full grid grid-cols-12 gap-4">
			<section className="p-5 flex shrink-0 bg-red-100 flex-1 h-full col-span-4 border-gray-300 rounded-md border-2">
				chat
			</section>
			<section className="p-5 border-gray-300 rounded-md border-2 col-span-8 flex flex-1">
				response
			</section>
		</main>
	);
}

export default App;
