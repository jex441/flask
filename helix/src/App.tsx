import { useState, useEffect, useRef } from "react";
import SystemResponse from "./SystemResponse";

function App() {
	const bottomRef = useRef<HTMLDivElement>(null);
	const bottomRef1 = useRef<HTMLDivElement>(null);

	const [data, setData] = useState([]);
	const [input, setInput] = useState("");

	const fetchData = async () => {
		try {
			let res = await fetch("http://127.0.0.1:8000/messages");
			if (!res.ok) {
				throw new Error(`HTTP error! status: ${res.status}`);
			}
			let d = await res.json();
			setData(d);
		} catch (error) {
			console.error("Failed to fetch data:", error);
		}
	};
	console.log(data);
	useEffect(() => {
		fetchData();
	}, []);

	const submitHandler = async () => {
		try {
			const response = await fetch("http://127.0.0.1:8000/messages", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(input),
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const data = await response.json();
			console.log("Success:", data);
		} catch (error) {
			console.error("Error:", error);
		}
	};

	const changeHandler = (e) => {
		e.preventDefault();
		setInput(e.target.value);
	};

	useEffect(() => {
		if (bottomRef.current) {
			bottomRef.current.scrollIntoView({ behavior: "auto" });
		}
	}, [data]);
	useEffect(() => {
		if (bottomRef1.current) {
			bottomRef1.current.scrollIntoView({ behavior: "auto" });
		}
	}, [data]);
	return (
		<main className="h-screen w-full grid grid-cols-12 gap-8 bg-gray-200/60">
			<section className="m-4 py-2 pl-2 overflow-y-auto overflow-x-hidden flex flex-col shrink-0 bg-white flex-1 max-h-full col-span-4 border-gray-300 rounded-md border-2">
				<ul className="h-[80%] overflow-y-auto">
					{data &&
						data.map((msg) => {
							if (msg.role === "user") {
								return (
									<li className="text-sm p-2 rounded-md m-2 bg-violet-500/40">
										{msg.content}
									</li>
								);
							}
							if (msg.role === "system") {
								return (
									<li className="text-sm p-2 rounded-md m-2 bg-emerald-500/60">
										{msg.content}
									</li>
								);
							}
						})}
					<div ref={bottomRef1} />
				</ul>
				<section>
					<form
						onSubmit={submitHandler}
						className="flex flex-col w-full flex p-3 gap-2"
					>
						<textarea
							placeholder="How can I help?"
							className="border-2 border-gray-300 p-2"
							value={input}
							onChange={(e) => changeHandler(e)}
						/>
						<button
							className="bg-black rounded-md text-white p-2"
							type="submit"
						>
							Submit
						</button>
					</form>
				</section>
			</section>

			{/* Data */}
			<section className="flex-col m-4 rounded-md overflow-y-auto overflow-x-hidden col-span-8 flex flex-1">
				<ul>
					{data &&
						data.map((msg) => {
							if (msg.data) {
								return (
									<SystemResponse
										data={msg.data}
										createdAt={msg.date_created}
									/>
								);
							}
						})}
				</ul>
				<div ref={bottomRef} />
			</section>
		</main>
	);
}

export default App;
